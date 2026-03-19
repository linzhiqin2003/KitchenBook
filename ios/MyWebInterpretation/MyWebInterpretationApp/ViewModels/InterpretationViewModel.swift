import Foundation
import SwiftUI
import Translation

@MainActor
final class InterpretationViewModel: ObservableObject {
    @Published var isRecording: Bool = false
    @Published var isPaused: Bool = false
    @Published var isBroadcasting: Bool = false
    @Published var sourceLang: String = "en"
    @Published var targetLang: String = "Chinese"
    @Published var segments: [SegmentResult] = []
    @Published var lastError: String?
    @Published var waveformLevels: [CGFloat] = Array(repeating: 0.04, count: 40)
    @Published var recordingSeconds: Int = 0
    @Published var localRecordings: [LocalInterpretationRecording] = []
    @Published var creditBalance: Int = UserDefaults.standard.integer(forKey: "cachedCreditBalance") {
        didSet { UserDefaults.standard.set(creditBalance, forKey: "cachedCreditBalance") }
    }
    private var recordingTimer: Timer?

    var authViewModel: AuthViewModel?

    @AppStorage("apiBaseURL") private var userBaseURL: String = ""
    @AppStorage("selectedAsrTier") var asrTier: String = "free"
    @AppStorage("speakerEnabled") var speakerEnabled: Bool = false
    @AppStorage("speakerProvider") var speakerProvider: String = "gpu"
    var translationSession: Any? = nil
    @AppStorage("vadEnabled") private var vadEnabled: Bool = true
    @AppStorage("vadThresholdDb") private var vadThresholdDb: Double = -50.0
    @AppStorage("vadSilenceMs") private var vadSilenceMs: Int = 300
    @AppStorage("maxSegmentSeconds") private var maxSegmentSeconds: Double = 4.0

    private let recorder = AudioSegmentRecorder()
    private let broadcastReceiver = BroadcastReceiver()
    private var broadcastSegmentSeq: Int = 0

    // Slow pipeline state
    private var currentParagraphSegmentIds: [UUID] = []
    private var slowPipelineTimer: Timer?
    // Must be longer than maxSegmentSeconds (~4s) so continuous speech accumulates
    // multiple segments before flushing. Pause/stop trigger immediate flush.
    private static let slowFlushDelay: TimeInterval = 5.0
    private var currentRecorderSessionID: UUID?
    private var segmentSessionMap: [UUID: UUID] = [:]
    private var pendingLocalArchives: [UUID: PendingLocalArchive] = [:]
    private var pendingLocalArchiveTasks: [UUID: Task<Void, Never>] = [:]
    private var completedSessionIDs: Set<UUID> = []
    private var speakerSessionId: String?

    private struct PendingLocalArchive {
        let sessionID: UUID
        let createdAt: Date
        let durationSeconds: TimeInterval
        let sourceLang: String
        let targetLang: String
        let audioURL: URL?
    }

    var apiBaseURL: String {
        if !userBaseURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return userBaseURL
        }
        return (Bundle.main.object(forInfoDictionaryKey: "MyWebAPIBaseURL") as? String) ?? "https://www.lzqqq.org"
    }

    var apiBaseURLBinding: Binding<String> {
        Binding(
            get: { self.apiBaseURL },
            set: { self.userBaseURL = $0 }
        )
    }

    /// Fast pipeline tier: Apple local for free, Groq/GPU for premium
    var fastPipelineTier: String {
        guard asrTier == "premium" else { return "local" }  // free → Apple on-device (WAV format)
        guard speakerEnabled else { return "free" }         // premium no speaker → Groq
        return speakerProvider == "tingwu" ? "speaker_tingwu" : "speaker_gpu"
    }

    /// Slow pipeline tier: Groq for free, DashScope for premium
    var slowPipelineTier: String {
        asrTier == "premium" ? "premium" : "free"
    }

    /// Slow pipeline always runs in live recording (fast ≠ slow for both tiers)
    var hasSlowPipeline: Bool { true }

    /// Segments visible in the UI — hides segments from completed (stopped) sessions
    /// while keeping them in memory for the slow pipeline and local archive to use.
    var visibleSegments: [SegmentResult] {
        segments.filter { seg in
            guard let sessionID = segmentSessionMap[seg.id] else { return true }
            return !completedSessionIDs.contains(sessionID)
        }
    }

    /// Whether the current configuration needs a speaker session ID
    var needsSpeakerSession: Bool {
        asrTier == "premium" && speakerEnabled && speakerProvider == "gpu"
    }

    init() {
        // Migrate old defaults and guard against out-of-range values.
        // .voiceChat mode suppresses volume: speech ~-37 to -50 dB, silence ~-55 to -78 dB.
        // Threshold of -50 dB works for both iPhone (with VPIO) and iPad (without VPIO).
        if vadThresholdDb < -60.0 || vadThresholdDb >= -20.0 {
            vadThresholdDb = -50.0
        } else if abs(vadThresholdDb - (-35.0)) < 0.01 || abs(vadThresholdDb - (-40.0)) < 0.01 {
            vadThresholdDb = -50.0
        }

        if vadSilenceMs < 150 || vadSilenceMs > 1500 {
            vadSilenceMs = 300
        } else if vadSilenceMs == 400 {
            vadSilenceMs = 300
        }

        if maxSegmentSeconds < 2.0 || maxSegmentSeconds > 10.0 {
            maxSegmentSeconds = 4.0
        } else if abs(maxSegmentSeconds - 5.0) < 0.01 {
            maxSegmentSeconds = 4.0
        }

        do {
            localRecordings = try LocalRecordingStore.loadRecordings()
        } catch {
            localRecordings = []
            print("[LocalArchive] load failed: \(error)")
        }

        recorder.onSegmentReady = { [weak self] fileURL, seq, recorderSessionID in
            Task { @MainActor in
                self?.handleSegment(fileURL: fileURL, seq: seq, recorderSessionID: recorderSessionID)
            }
        }

        recorder.onPowerUpdate = { [weak self] (power: Float) in
            let normalized = CGFloat(max(0, min(1, (power + 60) / 60)))
            let level = max(0.04, normalized)
            Task { @MainActor in
                guard let self = self, self.isRecording, !self.isPaused else { return }
                self.waveformLevels.append(level)
                if self.waveformLevels.count > 40 {
                    self.waveformLevels.removeFirst(self.waveformLevels.count - 40)
                }
            }
        }

    }

    func start() {
        print("🎙️ [VM] start() called")
        lastError = nil

        recorder.vadEnabled = vadEnabled
        recorder.vadThresholdDb = Float(vadThresholdDb)
        recorder.vadSilenceMs = vadSilenceMs
        recorder.maxSegmentSeconds = maxSegmentSeconds

        print("🎙️ [VM] VAD: enabled=\(vadEnabled) threshold=\(vadThresholdDb)dB silence=\(vadSilenceMs)ms maxSeg=\(maxSegmentSeconds)s")
        print("🎙️ [VM] API: \(apiBaseURL)")

        Task {
            do {
                print("🎙️ [VM] calling recorder.start()...")
                try await recorder.start()
                print("🎙️ [VM] recorder started OK")
                isRecording = true
                currentRecorderSessionID = recorder.sessionID
                speakerSessionId = needsSpeakerSession ? UUID().uuidString : nil
                self.recordingSeconds = 0
                self.recordingTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
                    Task { @MainActor in self?.recordingSeconds += 1 }
                }
            } catch {
                print("🎙️ [VM] recorder.start() FAILED: \(error)")
                lastError = error.friendlyMessage
                isRecording = false
            }
        }
    }

    func togglePause() {
        if !isPaused {
            print("🎙️ [VM] pause")
            recorder.pause()
            isPaused = true
            recordingTimer?.invalidate()
            recordingTimer = nil
            waveformLevels = Array(repeating: 0.04, count: 40)
            // Flush slow pipeline for segments accumulated so far
            flushSlowPipeline()
        } else {
            print("🎙️ [VM] resume")
            recorder.resume()
            isPaused = false
            self.recordingTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
                Task { @MainActor in self?.recordingSeconds += 1 }
            }
        }
    }

    func stopAndSave() {
        print("🎙️ [VM] stopAndSave()")
        let stoppingSessionID = currentRecorderSessionID
        let stoppingDuration = TimeInterval(recordingSeconds)
        let stoppingSourceLang = sourceLang
        let stoppingTargetLang = targetLang
        let stoppingAt = Date()

        recorder.stop()
        let completedSessionAudioURL = recorder.takeCompletedSessionAudioURL()

        isRecording = false
        isPaused = false
        currentRecorderSessionID = nil
        speakerSessionId = nil
        waveformLevels = Array(repeating: 0.04, count: 40)
        recordingTimer?.invalidate()
        recordingTimer = nil

        if let stoppingSessionID {
            // Hide this session's segments from UI immediately
            completedSessionIDs.insert(stoppingSessionID)

            queueLocalArchive(
                sessionID: stoppingSessionID,
                createdAt: stoppingAt,
                durationSeconds: stoppingDuration,
                sourceLang: stoppingSourceLang,
                targetLang: stoppingTargetLang,
                audioURL: completedSessionAudioURL
            )
        }

        // Flush slow pipeline on stop
        flushSlowPipeline()
    }

    func stopAndDiscard() {
        print("🎙️ [VM] stopAndDiscard()")
        recorder.stop()
        isRecording = false
        isPaused = false
        currentRecorderSessionID = nil
        speakerSessionId = nil
        waveformLevels = Array(repeating: 0.04, count: 40)
        recordingTimer?.invalidate()
        recordingTimer = nil
        slowPipelineTimer?.invalidate()
        slowPipelineTimer = nil
        currentParagraphSegmentIds.removeAll()
        clear()
    }

    func clear() {
        for seg in segments {
            segmentSessionMap.removeValue(forKey: seg.id)
        }
        segments.removeAll()
        lastError = nil
        currentParagraphSegmentIds.removeAll()
        slowPipelineTimer?.invalidate()
        slowPipelineTimer = nil
    }

    // MARK: - Broadcast (System Audio)

    func startBroadcastListening() {
        isBroadcasting = true
        broadcastSegmentSeq = 0
        segments.removeAll()
        lastError = nil

        broadcastReceiver.onSegmentReady = { [weak self] fileURL in
            Task { @MainActor in
                self?.handleBroadcastSegment(fileURL: fileURL)
            }
        }
        broadcastReceiver.onBroadcastStopped = { [weak self] in
            Task { @MainActor in
                self?.isBroadcasting = false
                self?.broadcastReceiver.stopListening()
            }
        }
        broadcastReceiver.startListening()
    }

    func stopBroadcastListening() {
        isBroadcasting = false
        broadcastReceiver.stopListening()
        broadcastReceiver.cleanupSegments()
    }

    private func handleBroadcastSegment(fileURL: URL) {
        broadcastSegmentSeq += 1
        // Reuse fast pipeline only (no slow pipeline / local archive for broadcast)
        handleSegment(fileURL: fileURL, seq: broadcastSegmentSeq, recorderSessionID: nil)
    }

    func uploadFile(url: URL) {
        guard url.startAccessingSecurityScopedResource() else {
            lastError = "Cannot access file"
            return
        }

        let tmpDir = FileManager.default.temporaryDirectory
        let tmpURL = tmpDir.appendingPathComponent(url.lastPathComponent)
        try? FileManager.default.removeItem(at: tmpURL)
        do {
            try FileManager.default.copyItem(at: url, to: tmpURL)
        } catch {
            lastError = error.friendlyMessage
            url.stopAccessingSecurityScopedResource()
            return
        }
        url.stopAccessingSecurityScopedResource()

        // Upload clears previous results and slow pipeline state
        for seg in segments {
            segmentSessionMap.removeValue(forKey: seg.id)
        }
        segments.removeAll()
        currentParagraphSegmentIds.removeAll()
        slowPipelineTimer?.invalidate()
        slowPipelineTimer = nil
        lastError = nil

        handleSegment(fileURL: tmpURL, seq: 1, recorderSessionID: nil)
    }

    // MARK: - Fast Pipeline

    private func handleSegment(fileURL: URL, seq: Int, recorderSessionID: UUID?) {
        let t0 = CFAbsoluteTimeGetCurrent()
        print("⏱️ [Seg#\(seq)] created at \(String(format: "%.3f", t0))")
        let segment = SegmentResult(seq: seq)
        segments.append(segment)

        if let recorderSessionID {
            segmentSessionMap[segment.id] = recorderSessionID
        }

        let isCurrentRecorderSession =
            isRecording &&
            !isPaused &&
            recorderSessionID != nil &&
            recorderSessionID == currentRecorderSessionID
        let shouldEnterSlowPipeline = isCurrentRecorderSession && hasSlowPipeline
        if shouldEnterSlowPipeline {
            currentParagraphSegmentIds.append(segment.id)
        }

        let segmentId = segment.id
        let sourceLang = self.sourceLang
        let targetLang = self.targetLang
        let baseURLString = self.apiBaseURL
        let token = KeychainService.load(.accessToken)
        let authVM = self.authViewModel

        // Fast pipeline: Apple local for free, Groq/GPU for premium
        let fastAsrTier = self.fastPipelineTier
        let currentSpeakerSessionId = self.needsSpeakerSession ? self.speakerSessionId : nil
        // When slow pipeline follows, fast result is preliminary (shows shimmer);
        // otherwise fast result is already final.
        let fastIsFinal = !shouldEnterSlowPipeline
        let translationSessionRef = self.translationSession

        if fastAsrTier == "local" {
            // Free mode fast pipeline: Apple on-device ASR first, Groq fallback if empty
            Task.detached {
                let asrStart = CFAbsoluteTimeGetCurrent()
                print("⏱️ [Seg#\(seq)] AppleASR start (+\(String(format: "%.0f", (asrStart - t0) * 1000))ms)")
                let transcription = await AppleSpeechService.shared.transcribe(
                    fileURL: fileURL,
                    locale: AppleSpeechService.locale(for: sourceLang)
                )
                let asrEnd = CFAbsoluteTimeGetCurrent()
                var text = transcription ?? ""
                print("⏱️ [Seg#\(seq)] AppleASR done (+\(String(format: "%.0f", (asrEnd - t0) * 1000))ms) text=\(text.isEmpty ? "(empty)" : "\"\(text.prefix(60))\"")")

                var translatedText = ""

                if text.isEmpty || Self.isHallucination(text) {
                    // Apple ASR failed — fall back to Groq for instant result
                    print("⏱️ [Seg#\(seq)] AppleASR empty → Groq fallback")
                    do {
                        let result = try await self.callTranscribeTranslate(
                            fileURL: fileURL,
                            baseURLString: baseURLString,
                            sourceLang: sourceLang,
                            targetLang: targetLang,
                            token: token,
                            authVM: authVM,
                            asrTier: "free"
                        )
                        let groqDone = CFAbsoluteTimeGetCurrent()
                        print("⏱️ [Seg#\(seq)] Groq fallback done (+\(String(format: "%.0f", (groqDone - t0) * 1000))ms) asr=GroqWhisper translate=GroqQwen text=\"\(result.transcription.prefix(60))\"")

                        if !result.transcription.isEmpty && !Self.isHallucination(result.transcription) {
                            text = result.transcription
                            translatedText = result.translation
                        }
                    } catch {
                        print("⏱️ [Seg#\(seq)] Groq fallback error: \(error)")
                    }
                } else {
                    // Apple ASR succeeded — translate locally (iOS 18+)
                    if #available(iOS 18.0, *),
                       let session = translationSessionRef as? TranslationSession {
                        do {
                            let response = try await session.translate(text)
                            translatedText = response.targetText
                            print("⏱️ [Seg#\(seq)] translate=AppleTranslation")
                        } catch {
                            print("⏱️ [Seg#\(seq)] AppleTranslation error: \(error)")
                        }
                    } else {
                        print("⏱️ [Seg#\(seq)] translate=none (iOS<18, no Translation session)")
                    }
                }

                if text.isEmpty || Self.isHallucination(text) {
                    // Both Apple ASR and Groq fallback returned empty
                    print("⏱️ [Seg#\(seq)] both pipelines empty")
                    if fastIsFinal {
                        await MainActor.run {
                            self.updateSegment(id: segmentId) { seg in
                                seg.transcription = ""
                                seg.translation = ""
                                seg.status = .done
                                seg.isFinal = true
                            }
                        }
                    }
                } else {
                    let translation = translatedText
                    let done = CFAbsoluteTimeGetCurrent()
                    print("⏱️ [Seg#\(seq)] fast done (+\(String(format: "%.0f", (done - t0) * 1000))ms) isFinal=\(fastIsFinal)")
                    print("⏱️ [Seg#\(seq)]   text=\"\(text.prefix(60))\"  translation=\"\(translation.prefix(60))\"")
                    await MainActor.run {
                        self.updateSegment(id: segmentId) { seg in
                            seg.transcription = text
                            seg.translation = translation
                            seg.status = .done
                            seg.isFinal = fastIsFinal
                        }
                    }
                }
                // Don't delete file — slow pipeline needs it via accumulated audio
            }
        } else {
            // Premium mode fast pipeline: Groq / GPU / TingWu (network)
            Task.detached {
                do {
                    let result = try await self.callTranscribeTranslate(
                        fileURL: fileURL,
                        baseURLString: baseURLString,
                        sourceLang: sourceLang,
                        targetLang: targetLang,
                        token: token,
                        authVM: authVM,
                        asrTier: fastAsrTier,
                        sessionId: currentSpeakerSessionId
                    )
                    print("[Fast] Got result: \(result.transcription.prefix(50))... speaker=\(result.speaker_id ?? "nil")")

                    // Filter ASR hallucinations (common phantom outputs on low-energy audio)
                    if Self.isHallucination(result.transcription) {
                        print("[Fast] Filtered hallucination: \"\(result.transcription)\"")
                        await MainActor.run {
                            self.updateSegment(id: segmentId) { seg in
                                seg.transcription = ""
                                seg.translation = ""
                                seg.status = .done
                                seg.isFinal = true
                            }
                        }
                    } else {
                        await MainActor.run {
                            self.updateSegment(id: segmentId) { seg in
                                seg.transcription = result.transcription
                                seg.translation = result.translation
                                seg.status = .done
                                seg.speakerId = result.speaker_id
                                seg.isFinal = fastIsFinal
                            }
                            // Clear fast-pipeline errors now that API is responding,
                            // but preserve slow-pipeline errors (prefixed with [慢管道])
                            if let err = self.lastError, !err.hasPrefix("[慢管道]") {
                                self.lastError = nil
                            }
                        }
                    }
                } catch let error as APIError where error.isGroqKeyRevoked {
                    print("[Fast] Groq key revoked, stopping recording")
                    await MainActor.run {
                        self.lastError = error.friendlyMessage
                        self.stopAndSave()
                    }
                } catch {
                    print("[Fast] Network error for segment #\(seq): \(error), trying local fallback...")

                    // Attempt local offline fallback
                    let localResult = await self.attemptLocalFallback(
                        fileURL: fileURL, sourceLang: sourceLang, targetLang: targetLang
                    )
                    if let local = localResult {
                        print("[Fast] Local fallback succeeded: \(local.transcription.prefix(50))...")
                        await MainActor.run {
                            self.updateSegment(id: segmentId) { seg in
                                seg.transcription = local.transcription
                                seg.translation = local.translation
                                seg.status = .done
                                seg.isOffline = true
                                seg.isFinal = true
                            }
                        }
                    } else {
                        print("[Fast] Local fallback unavailable for segment #\(seq)")
                        await MainActor.run {
                            self.updateSegment(id: segmentId) { seg in
                                seg.status = .error
                                seg.errorMessage = error.friendlyMessage
                            }
                            self.lastError = error.friendlyMessage
                        }
                    }
                }
                try? FileManager.default.removeItem(at: fileURL)
            }
        }

        // Schedule slow pipeline flush only for live recording segments.
        if shouldEnterSlowPipeline {
            scheduleSlowPipeline()
        }
    }

    /// Calls transcribeTranslate with auto-retry on 401 (token refresh).
    private func callTranscribeTranslate(
        fileURL: URL,
        baseURLString: String,
        sourceLang: String,
        targetLang: String,
        token: String?,
        authVM: AuthViewModel?,
        asrTier: String = "free",
        sessionId: String? = nil
    ) async throws -> TranscribeTranslateResponse {
        let client = try APIClient(baseURLString: baseURLString, accessToken: token)
        do {
            let result = try await client.transcribeTranslate(
                fileURL: fileURL,
                sourceLang: sourceLang,
                targetLang: targetLang,
                asrTier: asrTier,
                sessionId: sessionId
            )
            // Update balance if returned
            if let balance = result.balance_seconds {
                await MainActor.run { self.creditBalance = balance }
            }
            return result
        } catch APIError.groqKeyRevoked {
            // Key was revoked server-side, refresh user profile and stop
            await MainActor.run {
                authVM?.user?.has_groq_key = false
            }
            throw APIError.groqKeyRevoked
        } catch APIError.unauthorized {
            // Try refreshing the token
            if let authVM = authVM {
                let refreshed = await authVM.refreshAccessToken()
                if refreshed, let newToken = KeychainService.load(.accessToken) {
                    let retryClient = try APIClient(baseURLString: baseURLString, accessToken: newToken)
                    let result = try await retryClient.transcribeTranslate(
                        fileURL: fileURL,
                        sourceLang: sourceLang,
                        targetLang: targetLang,
                        asrTier: asrTier,
                        sessionId: sessionId
                    )
                    if let balance = result.balance_seconds {
                        await MainActor.run { self.creditBalance = balance }
                    }
                    return result
                }
            }
            throw APIError.unauthorized
        } catch APIError.insufficientCredits(let balance, _) {
            await MainActor.run {
                self.creditBalance = balance
                if balance <= 0 {
                    self.asrTier = "free"
                }
            }
            throw APIError.insufficientCredits(balance: balance, required: 0)
        }
    }

    func fetchCreditBalance() async {
        guard let token = KeychainService.load(.accessToken) else { return }
        do {
            let service = try CreditService(baseURLString: apiBaseURL, accessToken: token)
            let response = try await service.getBalance()
            self.creditBalance = response.balance_seconds
        } catch APIError.unauthorized {
            // Token expired — try refresh and retry once
            if let authVM = authViewModel {
                let refreshed = await authVM.refreshAccessToken()
                if refreshed, let newToken = KeychainService.load(.accessToken) {
                    do {
                        let retryService = try CreditService(baseURLString: apiBaseURL, accessToken: newToken)
                        let response = try await retryService.getBalance()
                        self.creditBalance = response.balance_seconds
                    } catch {
                        print("[Credits] fetchBalance retry error: \(error)")
                    }
                }
            }
        } catch {
            print("[Credits] fetchBalance error: \(error)")
        }
    }

    // MARK: - Slow Pipeline

    private func scheduleSlowPipeline() {
        // "Set once, don't reset": only start a timer if one isn't already running.
        // This lets segments accumulate during continuous speech instead of
        // resetting the timer on every new segment (which would prevent it from
        // ever firing when segment interval < delay).
        guard slowPipelineTimer == nil else { return }
        slowPipelineTimer = Timer.scheduledTimer(
            withTimeInterval: Self.slowFlushDelay,
            repeats: false
        ) { [weak self] _ in
            Task { @MainActor in
                self?.flushSlowPipeline()
            }
        }
    }

    private func flushSlowPipeline() {
        slowPipelineTimer?.invalidate()
        slowPipelineTimer = nil

        let entryIds = currentParagraphSegmentIds
        currentParagraphSegmentIds = []

        guard !entryIds.isEmpty else { return }

        guard let accumulatedURL = recorder.flushAccumulatedAudio() else {
            print("[Slow] No accumulated audio available")
            return
        }

        // Validate accumulated audio file before sending
        let fileSize: Int
        do {
            let attrs = try FileManager.default.attributesOfItem(atPath: accumulatedURL.path)
            fileSize = (attrs[.size] as? Int) ?? 0
        } catch {
            print("[Slow] Cannot read accumulated file attributes: \(error)")
            for entryId in entryIds { updateSegment(id: entryId) { $0.isFinal = true } }
            return
        }
        if fileSize < 100 {
            print("[Slow] Accumulated audio too small (\(fileSize) bytes), skipping")
            try? FileManager.default.removeItem(at: accumulatedURL)
            for entryId in entryIds { updateSegment(id: entryId) { $0.isFinal = true } }
            return
        }

        let sourceLang = self.sourceLang
        let targetLang = self.targetLang
        let baseURLString = self.apiBaseURL
        let token = KeychainService.load(.accessToken)
        let authVM = self.authViewModel
        // Slow pipeline: use DashScope (premium) for quality, no speaker session
        let slowAsrTier = self.slowPipelineTier

        let slowT0 = CFAbsoluteTimeGetCurrent()
        let slowModels = slowAsrTier == "free" ? "asr=GroqWhisper translate=GroqQwen" : "asr=DashScope translate=Cerebras"
        print("⏱️ [Slow] flush \(entryIds.count) segs, tier=\(slowAsrTier) (\(slowModels)), audioSize=\(fileSize)B")

        Task.detached {
            defer { try? FileManager.default.removeItem(at: accumulatedURL) }

            do {
                print("⏱️ [Slow] API call start (+\(String(format: "%.0f", (CFAbsoluteTimeGetCurrent() - slowT0) * 1000))ms)")
                let result = try await self.callTranscribeTranslate(
                    fileURL: accumulatedURL,
                    baseURLString: baseURLString,
                    sourceLang: sourceLang,
                    targetLang: targetLang,
                    token: token,
                    authVM: authVM,
                    asrTier: slowAsrTier
                )

                let slowElapsed = CFAbsoluteTimeGetCurrent() - slowT0
                print("⏱️ [Slow] API done (+\(String(format: "%.0f", slowElapsed * 1000))ms) text=\"\(result.transcription.prefix(80))\"")

                let primaryId = entryIds[0]
                let slowTranscription = result.transcription

                // Check if fast pipeline had no text (e.g. Apple ASR returned empty)
                let fastHadNoText = await MainActor.run {
                    self.segments.first(where: { $0.id == primaryId })?.transcription.isEmpty ?? true
                }

                print("⏱️ [Slow] fastHadNoText=\(fastHadNoText), will shimmer=\(fastHadNoText)")
                await MainActor.run {
                    for (i, entryId) in entryIds.enumerated() {
                        self.updateSegment(id: entryId) { seg in
                            if i == 0 {
                                seg.transcription = result.transcription
                                seg.translation = result.translation
                                seg.status = .done
                                // Show brief shimmer when fast pipeline had no preview text
                                seg.isFinal = !fastHadNoText
                            } else {
                                seg.transcription = ""
                                seg.translation = ""
                                seg.status = .done
                                seg.isFinal = true
                            }
                        }
                    }
                }

                // Brief shimmer flash for text that appeared without fast pipeline preview
                if fastHadNoText {
                    print("⏱️ [Slow] shimmer start (0.6s)")
                    try? await Task.sleep(nanoseconds: 600_000_000)
                    await MainActor.run {
                        self.updateSegment(id: primaryId) { seg in
                            seg.isFinal = true
                        }
                    }
                    print("⏱️ [Slow] shimmer → final")
                }

                // Trigger refine pipeline for this paragraph
                if !slowTranscription.isEmpty {
                    await self.triggerRefine(
                        segmentId: primaryId,
                        text: slowTranscription,
                        sourceLang: sourceLang,
                        targetLang: targetLang,
                        baseURLString: baseURLString,
                        token: token
                    )
                }
            } catch let apiError as APIError {
                print("[Slow] API error (tier=\(slowAsrTier)): \(apiError)")
                // Promote fast pipeline results to final; also ensure status is .done
                // in case the fast pipeline left the segment as .uploading (e.g. local ASR returned empty).
                await MainActor.run {
                    for entryId in entryIds {
                        self.updateSegment(id: entryId) { seg in
                            seg.status = .done
                            seg.isFinal = true
                        }
                    }
                    self.lastError = "[慢管道] \(apiError.friendlyMessage)"
                }
            } catch {
                print("[Slow] Unexpected error (tier=\(slowAsrTier)): \(error)")
                await MainActor.run {
                    for entryId in entryIds {
                        self.updateSegment(id: entryId) { seg in
                            seg.status = .done
                            seg.isFinal = true
                        }
                    }
                    self.lastError = "[慢管道] \(error.friendlyMessage)"
                }
            }
        }
    }

    // MARK: - Refine Pipeline

    private func triggerRefine(
        segmentId: UUID,
        text: String,
        sourceLang: String,
        targetLang: String,
        baseURLString: String,
        token: String?
    ) async {
        print("[Refine] Starting for segment, text: \(text.prefix(60))...")
        do {
            let client = try APIClient(baseURLString: baseURLString, accessToken: token)
            let result = try await client.refineTranscription(
                text: text,
                sourceLang: sourceLang,
                targetLang: targetLang
            )
            print("[Refine] Done: \(result.refined_transcription.prefix(60))...")

            await MainActor.run {
                self.updateSegment(id: segmentId) { seg in
                    seg.transcription = result.refined_transcription
                    seg.translation = result.translation
                    seg.isRefined = true
                }
            }
        } catch {
            print("[Refine] Error: \(error)")
            // Refinement failure is non-critical, keep slow pipeline result
        }
    }

    // MARK: - ASR Hallucination Filter

    /// Known ASR hallucination phrases produced on low-energy or near-silent audio.
    private nonisolated static let hallucinationPatterns: Set<String> = [
        "thank you", "thank you.", "thank you!", "thanks.",
        "thanks for watching", "thanks for watching.",
        "thanks for listening", "thanks for listening.",
        "subscribe", "like and subscribe",
        "bye", "bye.", "bye bye", "goodbye",
        "you", "the end", "the end.",
        "字幕由amara.org社区提供",
        "谢谢观看", "谢谢", "感谢收看",
        "请订阅", "再见",
    ]

    private nonisolated static func isHallucination(_ text: String) -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { return true }
        // Exact match against known patterns
        if hallucinationPatterns.contains(trimmed.lowercased()) { return true }
        // Very short text (≤3 chars) is likely noise
        if trimmed.count <= 3 { return true }
        // Repeated punctuation or whitespace only
        if trimmed.allSatisfy({ $0.isPunctuation || $0.isWhitespace }) { return true }
        return false
    }

    // MARK: - Local Offline Fallback

    /// Attempt local on-device transcription + translation. Returns nil if unavailable.
    private nonisolated func attemptLocalFallback(
        fileURL: URL,
        sourceLang: String,
        targetLang: String
    ) async -> LocalPipelineResult? {
        guard #available(iOS 26, *) else { return nil }
        guard LocalPipelineService.isAvailable(sourceLang: sourceLang, targetLang: targetLang) else {
            return nil
        }
        do {
            return try await LocalPipelineService.transcribeAndTranslate(
                fileURL: fileURL,
                sourceLang: sourceLang,
                targetLang: targetLang
            )
        } catch {
            print("[LocalFallback] Error: \(error)")
            return nil
        }
    }

    // MARK: - Helpers

    private func updateSegment(id: UUID, mutate: (inout SegmentResult) -> Void) {
        guard let idx = segments.firstIndex(where: { $0.id == id }) else { return }
        var seg = segments[idx]
        mutate(&seg)
        segments[idx] = seg
    }

    // MARK: - Local Archive

    func deleteLocalRecording(_ recording: LocalInterpretationRecording) {
        do {
            try LocalRecordingStore.deleteRecording(id: recording.id)
            localRecordings.removeAll(where: { $0.id == recording.id })
        } catch {
            lastError = error.friendlyMessage
        }
    }

    func audioURL(for recording: LocalInterpretationRecording) -> URL? {
        LocalRecordingStore.audioURL(for: recording)
    }

    private func queueLocalArchive(
        sessionID: UUID,
        createdAt: Date,
        durationSeconds: TimeInterval,
        sourceLang: String,
        targetLang: String,
        audioURL: URL?
    ) {
        let pending = PendingLocalArchive(
            sessionID: sessionID,
            createdAt: createdAt,
            durationSeconds: durationSeconds,
            sourceLang: sourceLang,
            targetLang: targetLang,
            audioURL: audioURL
        )
        pendingLocalArchives[sessionID] = pending

        pendingLocalArchiveTasks[sessionID]?.cancel()
        pendingLocalArchiveTasks[sessionID] = Task { [weak self] in
            await self?.waitAndFinalizeLocalArchive(sessionID: sessionID)
        }
    }

    private func waitAndFinalizeLocalArchive(sessionID: UUID) async {
        // Wait up to 60s for async fast/slow pipeline to settle for this session.
        for _ in 0..<120 {
            if Task.isCancelled { return }

            let hasPending = segments.contains { seg in
                guard segmentSessionMap[seg.id] == sessionID else { return false }
                return seg.status != .done && seg.status != .error
            }
            if !hasPending {
                break
            }
            try? await Task.sleep(nanoseconds: 500_000_000)
        }

        finalizeLocalArchive(sessionID: sessionID)
    }

    private func finalizeLocalArchive(sessionID: UUID) {
        pendingLocalArchiveTasks[sessionID] = nil
        guard let pending = pendingLocalArchives.removeValue(forKey: sessionID) else { return }

        let sessionSegments = segments.filter { seg in
            segmentSessionMap[seg.id] == sessionID
        }

        let transcription = Self.joinWithSpeakerLabels(sessionSegments, keyPath: \.transcription)
        let translation = Self.joinWithSpeakerLabels(sessionSegments, keyPath: \.translation)

        // Clean up: remove session segments from memory and maps
        cleanupSessionSegments(sessionID: sessionID)

        if transcription.isEmpty, translation.isEmpty, pending.audioURL == nil {
            return
        }

        let createdAt = pending.createdAt
        let durationSeconds = pending.durationSeconds
        let sourceLang = pending.sourceLang
        let targetLang = pending.targetLang
        let audioURL = pending.audioURL
        let baseURLString = self.apiBaseURL
        let token = KeychainService.load(.accessToken)

        // Prefer Cerebras-generated title, fall back to local extraction
        let localTitle = localRecordingTitle(
            transcription: transcription,
            translation: translation
        )

        Task { [weak self] in
            // Try remote title generation first
            var title = localTitle
            do {
                let client = try APIClient(baseURLString: baseURLString, accessToken: token)
                let preferred = !translation.isEmpty ? translation : transcription
                if !preferred.isEmpty {
                    let generated = try await client.generateTitle(text: preferred)
                    if !generated.isEmpty {
                        title = generated
                        print("[LocalArchive] Cerebras title: \(title)")
                    }
                }
            } catch {
                print("[LocalArchive] generateTitle failed, using local: \(error)")
            }

            // Ensure uniqueness
            guard let self else { return }
            title = self.uniquedLocalRecordingTitle(title)

            do {
                let finalTitle = title
                let saved = try await Task.detached(priority: .utility) {
                    try LocalRecordingStore.addRecording(
                        createdAt: createdAt,
                        title: finalTitle,
                        durationSeconds: durationSeconds,
                        sourceLang: sourceLang,
                        targetLang: targetLang,
                        transcription: transcription,
                        translation: translation,
                        audioTempURL: audioURL
                    )
                }.value
                self.localRecordings.insert(saved, at: 0)
            } catch {
                if let audioURL {
                    try? FileManager.default.removeItem(at: audioURL)
                }
                self.lastError = error.friendlyMessage
            }
        }
    }

    private func cleanupSessionSegments(sessionID: UUID) {
        let idsToRemove = segments
            .filter { segmentSessionMap[$0.id] == sessionID }
            .map(\.id)
        segments.removeAll { segmentSessionMap[$0.id] == sessionID }
        for id in idsToRemove {
            segmentSessionMap.removeValue(forKey: id)
        }
        completedSessionIDs.remove(sessionID)
    }

    /// Join segment texts with 【S1】/【S2】 labels on speaker change.
    private static func joinWithSpeakerLabels(
        _ segments: [SegmentResult],
        keyPath: KeyPath<SegmentResult, String>
    ) -> String {
        var parts: [String] = []
        var lastSpeakerId: String? = nil

        for seg in segments {
            let text = seg[keyPath: keyPath].trimmingCharacters(in: .whitespacesAndNewlines)
            if text.isEmpty { continue }

            if let currentSpeaker = seg.speakerId, currentSpeaker != lastSpeakerId {
                // Extract short label: "speaker_0" → "S1", "speaker_1" → "S2"
                let label: String
                if let numStr = currentSpeaker.split(separator: "_").last,
                   let num = Int(numStr) {
                    label = "S\(num + 1)"
                } else {
                    label = currentSpeaker
                }
                parts.append("\n【\(label)】\(text)")
                lastSpeakerId = currentSpeaker
            } else {
                parts.append(text)
            }
        }

        return parts.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func localRecordingTitle(
        transcription: String,
        translation: String
    ) -> String {
        let preferred = !translation.isEmpty ? translation : transcription
        let normalized = normalizeTitleSource(preferred)
        let base = firstPhraseTitle(from: normalized) ?? "新录音"
        return uniquedLocalRecordingTitle(base)
    }

    private func normalizeTitleSource(_ text: String) -> String {
        // Strip speaker labels like 【S1】before extracting title
        var cleaned = text
        let labelPattern = try? NSRegularExpression(pattern: "【S\\d+】", options: [])
        if let regex = labelPattern {
            cleaned = regex.stringByReplacingMatches(
                in: cleaned, range: NSRange(cleaned.startIndex..., in: cleaned), withTemplate: ""
            )
        }
        return cleaned
            .replacingOccurrences(of: "\n", with: " ")
            .split(whereSeparator: \.isWhitespace)
            .joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func firstPhraseTitle(from text: String) -> String? {
        guard !text.isEmpty else { return nil }

        let splitSet = CharacterSet(charactersIn: "。！？!?；;：:\u{2026}")
        let rawPhrase = text.components(separatedBy: splitSet).first ?? text
        let trimmed = rawPhrase.trimmingCharacters(
            in: CharacterSet(charactersIn: " \t\r\n\"'“”‘’()[]{}<>，,、.。！？!?;:：-—_")
        )
        guard !trimmed.isEmpty else { return nil }

        let hasCJK = trimmed.unicodeScalars.contains(where: { scalar in
            (0x4E00...0x9FFF).contains(scalar.value)
        })
        let maxLength = hasCJK ? 14 : 24
        var candidate = String(trimmed.prefix(maxLength))

        // Prefer whole words for Latin scripts when truncating.
        if !hasCJK, trimmed.count > maxLength, let cut = candidate.lastIndex(of: " "), cut > candidate.startIndex {
            candidate = String(candidate[..<cut])
        }

        let validChars = candidate.unicodeScalars.filter { scalar in
            CharacterSet.alphanumerics.contains(scalar) || (0x4E00...0x9FFF).contains(scalar.value)
        }
        guard validChars.count >= 2 else { return nil }
        return candidate
    }

    private func uniquedLocalRecordingTitle(_ base: String) -> String {
        let existing = Set(localRecordings.map(\.title))
        guard existing.contains(base) else { return base }

        var index = 2
        while existing.contains("\(base) \(index)") {
            index += 1
        }
        return "\(base) \(index)"
    }
}
