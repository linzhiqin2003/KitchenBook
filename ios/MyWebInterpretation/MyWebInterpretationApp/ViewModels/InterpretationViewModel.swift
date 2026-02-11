import Foundation
import SwiftUI

@MainActor
final class InterpretationViewModel: ObservableObject {
    @Published var isRecording: Bool = false
    @Published var isPaused: Bool = false
    @Published var sourceLang: String = "en"
    @Published var targetLang: String = "Chinese"
    @Published var segments: [SegmentResult] = []
    @Published var lastError: String?
    @Published var waveformLevels: [CGFloat] = Array(repeating: 0.04, count: 40)
    @Published var recordingSeconds: Int = 0
    @Published var localRecordings: [LocalInterpretationRecording] = []
    @Published var creditBalance: Int = 0
    private var recordingTimer: Timer?

    var authViewModel: AuthViewModel?

    @AppStorage("apiBaseURL") private var userBaseURL: String = ""
    @AppStorage("selectedAsrTier") var asrTier: String = "free"
    @AppStorage("vadEnabled") private var vadEnabled: Bool = true
    @AppStorage("vadThresholdDb") private var vadThresholdDb: Double = -40.0
    @AppStorage("vadSilenceMs") private var vadSilenceMs: Int = 300
    @AppStorage("maxSegmentSeconds") private var maxSegmentSeconds: Double = 4.0

    private let recorder = AudioSegmentRecorder()

    // Slow pipeline state
    private var currentParagraphSegmentIds: [UUID] = []
    private var slowPipelineTimer: Timer?
    private static let slowFlushDelay: TimeInterval = 1.0
    private var currentRecorderSessionID: UUID?
    private var segmentSessionMap: [UUID: UUID] = [:]
    private var pendingLocalArchives: [UUID: PendingLocalArchive] = [:]
    private var pendingLocalArchiveTasks: [UUID: Task<Void, Never>] = [:]

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

    init() {
        // Migrate old defaults and guard against out-of-range values.
        if vadThresholdDb <= -50.0 || vadThresholdDb >= -20.0 {
            vadThresholdDb = -40.0
        } else if abs(vadThresholdDb - (-35.0)) < 0.01 {
            vadThresholdDb = -40.0
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
        waveformLevels = Array(repeating: 0.04, count: 40)
        recordingTimer?.invalidate()
        recordingTimer = nil

        if let stoppingSessionID {
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
        print("[Fast] handleSegment #\(seq)")
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
        let shouldEnterSlowPipeline = isCurrentRecorderSession
        if shouldEnterSlowPipeline {
            currentParagraphSegmentIds.append(segment.id)
        }

        let segmentId = segment.id
        let sourceLang = self.sourceLang
        let targetLang = self.targetLang
        let baseURLString = self.apiBaseURL
        let token = KeychainService.load(.accessToken)
        let authVM = self.authViewModel

        // Fast pipeline always uses free tier (Groq Whisper) for speed.
        // Premium DashScope ASR is only used in the slow pipeline.
        let fastAsrTier = "free"

        Task.detached {
            do {
                let result = try await self.callTranscribeTranslate(
                    fileURL: fileURL,
                    baseURLString: baseURLString,
                    sourceLang: sourceLang,
                    targetLang: targetLang,
                    token: token,
                    authVM: authVM,
                    asrTier: fastAsrTier
                )
                print("[Fast] Got result: \(result.transcription.prefix(50))...")

                await MainActor.run {
                    self.updateSegment(id: segmentId) { seg in
                        seg.transcription = result.transcription
                        seg.translation = result.translation
                        seg.status = .done
                        // Non-recording uploads and tail segments after stop
                        // have no slow pipeline pass, so fast result is final.
                        if !shouldEnterSlowPipeline {
                            seg.isFinal = true
                        }
                    }
                    // Clear any previous error (e.g. 502) now that API is responding
                    if self.lastError != nil {
                        self.lastError = nil
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
                            if !shouldEnterSlowPipeline {
                                seg.isFinal = true
                            }
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
        asrTier: String = "free"
    ) async throws -> TranscribeTranslateResponse {
        let client = try APIClient(baseURLString: baseURLString, accessToken: token)
        do {
            let result = try await client.transcribeTranslate(
                fileURL: fileURL,
                sourceLang: sourceLang,
                targetLang: targetLang,
                asrTier: asrTier
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
                        asrTier: asrTier
                    )
                    if let balance = result.balance_seconds {
                        await MainActor.run { self.creditBalance = balance }
                    }
                    return result
                }
            }
            throw APIError.unauthorized
        } catch APIError.insufficientCredits(let balance, _) {
            await MainActor.run { self.creditBalance = balance }
            throw APIError.insufficientCredits(balance: balance, required: 0)
        }
    }

    func fetchCreditBalance() async {
        guard let token = KeychainService.load(.accessToken) else { return }
        do {
            let service = try CreditService(baseURLString: apiBaseURL, accessToken: token)
            let response = try await service.getBalance()
            self.creditBalance = response.balance_seconds
        } catch {
            print("[Credits] fetchBalance error: \(error)")
        }
    }

    // MARK: - Slow Pipeline

    private func scheduleSlowPipeline() {
        slowPipelineTimer?.invalidate()
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

        print("[Slow] Flushing \(entryIds.count) segments")

        let sourceLang = self.sourceLang
        let targetLang = self.targetLang
        let baseURLString = self.apiBaseURL
        let token = KeychainService.load(.accessToken)
        let authVM = self.authViewModel
        let currentAsrTier = self.asrTier

        Task.detached {
            defer { try? FileManager.default.removeItem(at: accumulatedURL) }

            do {
                let result = try await self.callTranscribeTranslate(
                    fileURL: accumulatedURL,
                    baseURLString: baseURLString,
                    sourceLang: sourceLang,
                    targetLang: targetLang,
                    token: token,
                    authVM: authVM,
                    asrTier: currentAsrTier
                )

                print("[Slow] Got result: \(result.transcription.prefix(80))...")

                let primaryId = entryIds[0]
                let slowTranscription = result.transcription

                await MainActor.run {
                    for (i, entryId) in entryIds.enumerated() {
                        self.updateSegment(id: entryId) { seg in
                            if i == 0 {
                                seg.transcription = result.transcription
                                seg.translation = result.translation
                                seg.status = .done
                                seg.isFinal = true
                            } else {
                                seg.transcription = ""
                                seg.translation = ""
                                seg.status = .done
                                seg.isFinal = true
                            }
                        }
                    }
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
            } catch {
                print("[Slow] Network error: \(error), trying local fallback...")

                let localResult = await self.attemptLocalFallback(
                    fileURL: accumulatedURL, sourceLang: sourceLang, targetLang: targetLang
                )
                if let local = localResult {
                    print("[Slow] Local fallback succeeded")
                    await MainActor.run {
                        for (i, entryId) in entryIds.enumerated() {
                            self.updateSegment(id: entryId) { seg in
                                if i == 0 {
                                    seg.transcription = local.transcription
                                    seg.translation = local.translation
                                    seg.status = .done
                                    seg.isFinal = true
                                    seg.isOffline = true
                                } else {
                                    seg.transcription = ""
                                    seg.translation = ""
                                    seg.status = .done
                                    seg.isFinal = true
                                }
                            }
                        }
                    }
                } else {
                    print("[Slow] Local fallback also unavailable, marking segments as final with fast results")
                    await MainActor.run {
                        for entryId in entryIds {
                            self.updateSegment(id: entryId) { seg in
                                seg.isFinal = true
                            }
                        }
                    }
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

        let transcription = sessionSegments
            .map { $0.transcription.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: " ")

        let translation = sessionSegments
            .map { $0.translation.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: " ")

        if transcription.isEmpty, translation.isEmpty, pending.audioURL == nil {
            return
        }

        let title = localRecordingTitle(
            transcription: transcription,
            translation: translation
        )

        let createdAt = pending.createdAt
        let durationSeconds = pending.durationSeconds
        let sourceLang = pending.sourceLang
        let targetLang = pending.targetLang
        let audioURL = pending.audioURL

        Task { [weak self] in
            do {
                let saved = try await Task.detached(priority: .utility) {
                    try LocalRecordingStore.addRecording(
                        createdAt: createdAt,
                        title: title,
                        durationSeconds: durationSeconds,
                        sourceLang: sourceLang,
                        targetLang: targetLang,
                        transcription: transcription,
                        translation: translation,
                        audioTempURL: audioURL
                    )
                }.value
                guard let self else { return }
                self.localRecordings.insert(saved, at: 0)
            } catch {
                if let audioURL {
                    try? FileManager.default.removeItem(at: audioURL)
                }
                guard let self else { return }
                self.lastError = error.friendlyMessage
            }
        }
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
        text
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
