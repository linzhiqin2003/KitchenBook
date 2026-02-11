import Foundation
import SwiftUI

@MainActor
final class InterpretationViewModel: ObservableObject {
    @Published var isRecording: Bool = false
    @Published var sourceLang: String = "en"
    @Published var targetLang: String = "Chinese"
    @Published var segments: [SegmentResult] = []
    @Published var lastError: String?
    @Published var waveformLevels: [CGFloat] = Array(repeating: 0.04, count: 40)
    @Published var recordingSeconds: Int = 0
    private var recordingTimer: Timer?

    var authViewModel: AuthViewModel?

    @AppStorage("apiBaseURL") private var userBaseURL: String = ""
    @AppStorage("vadEnabled") private var vadEnabled: Bool = true
    @AppStorage("vadThresholdDb") private var vadThresholdDb: Double = -35.0
    @AppStorage("vadSilenceMs") private var vadSilenceMs: Int = 400
    @AppStorage("maxSegmentSeconds") private var maxSegmentSeconds: Double = 5.0

    private let recorder = AudioSegmentRecorder()

    // Slow pipeline state
    private var currentParagraphSegmentIds: [UUID] = []
    private var slowPipelineTimer: Timer?
    private static let slowFlushDelay: TimeInterval = 1.0

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
        // Migrate: reset to current default if stored value is from old configs
        if vadThresholdDb <= -50.0 || vadThresholdDb >= -20.0 {
            vadThresholdDb = -35.0
        }

        recorder.onSegmentReady = { [weak self] fileURL, seq in
            Task { @MainActor in
                self?.handleSegment(fileURL: fileURL, seq: seq)
            }
        }

        recorder.onPowerUpdate = { [weak self] (power: Float) in
            let normalized = CGFloat(max(0, min(1, (power + 60) / 60)))
            let level = max(0.04, normalized)
            Task { @MainActor in
                guard let self = self, self.isRecording else { return }
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
                self.recordingSeconds = 0
                self.recordingTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
                    Task { @MainActor in self?.recordingSeconds += 1 }
                }
            } catch {
                print("🎙️ [VM] recorder.start() FAILED: \(error)")
                lastError = error.localizedDescription
                isRecording = false
            }
        }
    }

    func stop() {
        print("🎙️ [VM] stop()")
        recorder.stop()
        isRecording = false
        waveformLevels = Array(repeating: 0.04, count: 40)
        recordingTimer?.invalidate()
        recordingTimer = nil

        // Flush slow pipeline on stop
        flushSlowPipeline()
    }

    func clear() {
        segments.removeAll()
        lastError = nil
        currentParagraphSegmentIds.removeAll()
        slowPipelineTimer?.invalidate()
        slowPipelineTimer = nil
    }

    private var uploadSeq: Int = 0

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
            lastError = error.localizedDescription
            url.stopAccessingSecurityScopedResource()
            return
        }
        url.stopAccessingSecurityScopedResource()

        // Upload clears previous results and slow pipeline state
        segments.removeAll()
        currentParagraphSegmentIds.removeAll()
        slowPipelineTimer?.invalidate()
        slowPipelineTimer = nil
        lastError = nil

        uploadSeq += 1
        handleSegment(fileURL: tmpURL, seq: 10000 + uploadSeq)
    }

    // MARK: - Fast Pipeline

    private func handleSegment(fileURL: URL, seq: Int) {
        print("[Fast] handleSegment #\(seq)")
        let segment = SegmentResult(seq: seq)
        segments.append(segment)
        currentParagraphSegmentIds.append(segment.id)

        let segmentId = segment.id
        let sourceLang = self.sourceLang
        let targetLang = self.targetLang
        let baseURLString = self.apiBaseURL
        let token = KeychainService.load(.accessToken)
        let authVM = self.authViewModel

        Task.detached {
            // Don't delete file on first attempt if we may retry
            var shouldDeleteFile = true
            do {
                let result = try await self.callTranscribeTranslate(
                    fileURL: fileURL,
                    baseURLString: baseURLString,
                    sourceLang: sourceLang,
                    targetLang: targetLang,
                    token: token,
                    authVM: authVM
                )
                print("[Fast] Got result: \(result.transcription.prefix(50))...")

                await MainActor.run {
                    self.updateSegment(id: segmentId) { seg in
                        seg.transcription = result.transcription
                        seg.translation = result.translation
                        seg.status = .done
                    }
                }
            } catch {
                print("[Fast] Error for segment #\(seq): \(error)")
                await MainActor.run {
                    self.updateSegment(id: segmentId) { seg in
                        seg.status = .error
                        seg.errorMessage = error.localizedDescription
                    }
                    self.lastError = error.localizedDescription
                }
            }
            try? FileManager.default.removeItem(at: fileURL)
        }

        // Schedule slow pipeline flush after silence
        scheduleSlowPipeline()
    }

    /// Calls transcribeTranslate with auto-retry on 401 (token refresh).
    private func callTranscribeTranslate(
        fileURL: URL,
        baseURLString: String,
        sourceLang: String,
        targetLang: String,
        token: String?,
        authVM: AuthViewModel?
    ) async throws -> TranscribeTranslateResponse {
        let client = try APIClient(baseURLString: baseURLString, accessToken: token)
        do {
            return try await client.transcribeTranslate(
                fileURL: fileURL,
                sourceLang: sourceLang,
                targetLang: targetLang
            )
        } catch APIError.unauthorized {
            // Try refreshing the token
            if let authVM = authVM {
                let refreshed = await authVM.refreshAccessToken()
                if refreshed, let newToken = KeychainService.load(.accessToken) {
                    let retryClient = try APIClient(baseURLString: baseURLString, accessToken: newToken)
                    return try await retryClient.transcribeTranslate(
                        fileURL: fileURL,
                        sourceLang: sourceLang,
                        targetLang: targetLang
                    )
                }
            }
            throw APIError.unauthorized
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

        Task.detached {
            defer { try? FileManager.default.removeItem(at: accumulatedURL) }

            do {
                let result = try await self.callTranscribeTranslate(
                    fileURL: accumulatedURL,
                    baseURLString: baseURLString,
                    sourceLang: sourceLang,
                    targetLang: targetLang,
                    token: token,
                    authVM: authVM
                )

                print("[Slow] Got result: \(result.transcription.prefix(80))...")

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
            } catch {
                print("[Slow] Error: \(error)")
            }
        }
    }

    // MARK: - Helpers

    private func updateSegment(id: UUID, mutate: (inout SegmentResult) -> Void) {
        guard let idx = segments.firstIndex(where: { $0.id == id }) else { return }
        var seg = segments[idx]
        mutate(&seg)
        segments[idx] = seg
    }
}
