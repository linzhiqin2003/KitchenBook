import AVFoundation
import Foundation

enum AudioRecorderError: LocalizedError {
    case microphonePermissionDenied
    case failedToConfigureAudioSession
    case failedToStartRecording

    var errorDescription: String? {
        switch self {
        case .microphonePermissionDenied:
            return "Microphone permission denied"
        case .failedToConfigureAudioSession:
            return "Failed to configure audio session"
        case .failedToStartRecording:
            return "Failed to start recording"
        }
    }
}

final class AudioSegmentRecorder {
    var vadEnabled: Bool = true
    var vadThresholdDb: Float = -40.0
    var vadSilenceMs: Int = 300
    var minSegmentSeconds: TimeInterval = 0.22
    var maxSegmentSeconds: TimeInterval = 5.0
    var onSegmentReady: ((URL, Int, UUID) -> Void)?
    var onPowerUpdate: ((Float) -> Void)?
    private(set) var isPaused: Bool = false

    private var engine: AVAudioEngine?
    private var recording = false
    private var seq: Int = 0
    private var meterTimer: Timer?
    private var segmentStartedAt: Date?
    private var segmentHasSpeech = false
    private var segmentSilenceMs: Int = 0
    private var segmentStopRequested = false
    private var currentSegmentURL: URL?
    private var currentPower: Float = -160.0
    private var segmentSumSquares: Double = 0
    private var segmentSampleCount: Int = 0
    private var segmentSpeechPolls: Int = 0
    private var segmentTotalPolls: Int = 0
    private static let minSegmentRMS: Float = 0.006
    private static let minSpeechRatio: Float = 0.08  // at least 8% of polls must detect speech
    private static let meterIntervalSeconds: TimeInterval = 0.04

    // Dual-file writing: segment file + accumulated file
    private var segmentFile: AVAudioFile?
    private var accumulatedFile: AVAudioFile?
    private var accumulatedURL: URL?
    private var sessionFile: AVAudioFile?
    private var sessionURL: URL?
    private var storedOutputSettings: [String: Any]?
    private let audioLock = NSLock()
    private(set) var sessionID: UUID = UUID()

    func start() async throws {
        print("🎙️ [Recorder] start() called, requesting mic permission...")
        let granted = await requestMicPermission()
        print("🎙️ [Recorder] mic permission granted=\(granted)")
        guard granted else { throw AudioRecorderError.microphonePermissionDenied }

        print("🎙️ [Recorder] configuring audio session...")
        try configureAudioSession()
        print("🎙️ [Recorder] audio session configured OK")

        let newEngine = AVAudioEngine()
        do {
            try newEngine.inputNode.setVoiceProcessingEnabled(true)
            newEngine.inputNode.isVoiceProcessingBypassed = false
            newEngine.inputNode.isVoiceProcessingAGCEnabled = true
            print("🎙️ [Recorder] voice processing enabled (AGC=on)")
        } catch {
            print("🎙️ [Recorder] voice processing unavailable: \(error)")
        }

        engine = newEngine
        recording = true
        sessionID = UUID()
        // Keep segment sequence monotonic across start/stop, so UI/export
        // ordering by seq always reflects timeline order.

        // Store output settings for reuse
        let hwFormat = newEngine.inputNode.outputFormat(forBus: 0)
        let tapFormat: AVAudioFormat?
        if hwFormat.sampleRate > 0, hwFormat.channelCount > 0 {
            tapFormat = hwFormat
        } else {
            // inputNode can return invalid format after audio session changes;
            // pass nil to let the engine use its native format.
            print("🎙️ [Recorder] inputNode format invalid (sr=\(hwFormat.sampleRate) ch=\(hwFormat.channelCount)), using nil")
            tapFormat = nil
        }
        let sampleRate = tapFormat?.sampleRate ?? AVAudioSession.sharedInstance().sampleRate
        storedOutputSettings = [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: sampleRate,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        ]

        // Install tap once — runs for entire recording session
        installTap(node: newEngine.inputNode, format: tapFormat)

        // Start session audio file for local archive
        startNewSessionFile()

        // Start accumulated audio file for slow pipeline
        startNewAccumulatedFile()

        // Open first segment file
        do {
            print("🎙️ [Recorder] starting first segment...")
            try openNewSegmentFile()
            print("🎙️ [Recorder] first segment started OK")
        } catch {
            print("🎙️ [Recorder] openNewSegmentFile FAILED: \(error)")
            stop()
            throw error
        }

        try newEngine.start()

        if vadEnabled {
            startMetering()
        }
    }

    func stop() {
        recording = false
        isPaused = false
        DispatchQueue.main.async { [weak self] in
            self?.meterTimer?.invalidate()
            self?.meterTimer = nil
        }

        // Finalize current segment
        finishCurrentSegment(discard: false)

        // Stop engine (stops tap from writing)
        engine?.stop()
        engine?.inputNode.removeTap(onBus: 0)
        engine = nil

        // Close accumulated file but keep URL for slow pipeline flush
        audioLock.lock()
        accumulatedFile = nil
        sessionFile = nil  // close session file, keep URL for local persistence
        audioLock.unlock()

        try? AVAudioSession.sharedInstance().setActive(false, options: [])
    }

    func pause() {
        guard recording, !isPaused else { return }
        isPaused = true

        // Finalize current segment so it enters the pipeline
        finishCurrentSegment(discard: false)

        // Pause engine — tap stays installed but we skip writes via isPaused flag
        engine?.pause()

        DispatchQueue.main.async { [weak self] in
            self?.meterTimer?.invalidate()
            self?.meterTimer = nil
        }
        print("🎙️ [Recorder] paused")
    }

    func resume() {
        guard recording, isPaused else { return }
        isPaused = false

        do {
            try engine?.start()
        } catch {
            print("🎙️ [Recorder] resume engine failed: \(error)")
            return
        }

        do {
            try openNewSegmentFile()
        } catch {
            print("🎙️ [Recorder] resume segment failed: \(error)")
            return
        }

        if vadEnabled {
            startMetering()
        }
        print("🎙️ [Recorder] resumed")
    }

    /// Flush accumulated audio for slow pipeline. Returns file URL or nil.
    func flushAccumulatedAudio() -> URL? {
        audioLock.lock()
        accumulatedFile = nil  // close current file
        let url = accumulatedURL
        accumulatedURL = nil

        // Start new accumulated file if still recording
        if recording, storedOutputSettings != nil {
            startNewAccumulatedFileUnlocked()
        }
        audioLock.unlock()

        return url
    }

    /// Returns completed full-session audio URL once and clears internal reference.
    func takeCompletedSessionAudioURL() -> URL? {
        audioLock.lock()
        let url = sessionURL
        sessionURL = nil
        audioLock.unlock()
        return url
    }

    // MARK: - Tap & File Management

    private func installTap(node: AVAudioInputNode, format: AVAudioFormat?) {
        // 1024 gives lower end-to-end latency while still being stable for VAD.
        node.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            guard let self = self else { return }

            // Skip all processing while paused
            if self.isPaused { return }

            // Compute RMS power from audio samples
            if let channelData = buffer.floatChannelData?[0] {
                let frameLength = Int(buffer.frameLength)
                var sumSquares: Float = 0
                for i in 0..<frameLength {
                    sumSquares += channelData[i] * channelData[i]
                }
                let rms = sqrt(sumSquares / max(Float(frameLength), 1))
                let power = 20 * log10(max(rms, 1e-10))
                self.currentPower = power
                self.onPowerUpdate?(power)

                // Accumulate energy for segment-level RMS check
                self.segmentSumSquares += Double(sumSquares)
                self.segmentSampleCount += frameLength
            }

            // Grab file references under lock (very brief), write outside lock
            self.audioLock.lock()
            let sf = self.segmentFile
            let af = self.accumulatedFile
            let full = self.sessionFile
            self.audioLock.unlock()

            if let sf = sf {
                do { try sf.write(from: buffer) } catch {
                    print("[Recorder] segment write error: \(error)")
                }
            }
            if let af = af {
                do { try af.write(from: buffer) } catch {
                    print("[Recorder] accumulated write error: \(error)")
                }
            }
            if let full = full {
                do { try full.write(from: buffer) } catch {
                    print("[Recorder] session write error: \(error)")
                }
            }
        }
    }

    private func openNewSegmentFile() throws {
        guard let settings = storedOutputSettings else {
            throw AudioRecorderError.failedToStartRecording
        }

        seq += 1
        segmentStopRequested = false
        segmentStartedAt = Date()
        segmentHasSpeech = false
        segmentSilenceMs = 0
        currentPower = -160.0
        segmentSumSquares = 0
        segmentSampleCount = 0
        segmentSpeechPolls = 0
        segmentTotalPolls = 0

        let dir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        let url = dir.appendingPathComponent("segment-\(seq)-\(UUID().uuidString).m4a")
        currentSegmentURL = url

        audioLock.lock()
        segmentFile = try AVAudioFile(forWriting: url, settings: settings)
        audioLock.unlock()
    }

    private func startNewAccumulatedFile() {
        audioLock.lock()
        startNewAccumulatedFileUnlocked()
        audioLock.unlock()
    }

    private func startNewSessionFile() {
        audioLock.lock()
        startNewSessionFileUnlocked()
        audioLock.unlock()
    }

    /// Must be called with audioLock held.
    private func startNewAccumulatedFileUnlocked() {
        guard let settings = storedOutputSettings else { return }
        let dir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        let url = dir.appendingPathComponent("accumulated-\(UUID().uuidString).m4a")
        accumulatedURL = url
        accumulatedFile = try? AVAudioFile(forWriting: url, settings: settings)
    }

    /// Must be called with audioLock held.
    private func startNewSessionFileUnlocked() {
        guard let settings = storedOutputSettings else { return }

        if let oldURL = sessionURL {
            try? FileManager.default.removeItem(at: oldURL)
        }

        let dir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        let url = dir.appendingPathComponent("session-\(sessionID.uuidString)-\(UUID().uuidString).m4a")
        sessionURL = url
        sessionFile = try? AVAudioFile(forWriting: url, settings: settings)
    }

    // MARK: - VAD Metering

    private func startMetering() {
        DispatchQueue.main.async { [weak self] in
            self?.meterTimer?.invalidate()
            self?.meterTimer = Timer.scheduledTimer(withTimeInterval: Self.meterIntervalSeconds, repeats: true) { [weak self] _ in
                self?.pollMeters()
            }
        }
    }

    private func pollMeters() {
        guard recording else { return }
        guard vadEnabled else { return }
        guard !segmentStopRequested else { return }
        guard let startedAt = segmentStartedAt else { return }

        let elapsed = Date().timeIntervalSince(startedAt)

        // Max segment duration
        if elapsed >= maxSegmentSeconds {
            stopCurrentSegment()
            return
        }

        let power = currentPower
        let isSpeech = power > vadThresholdDb
        segmentTotalPolls += 1
        if isSpeech { segmentSpeechPolls += 1 }

        // Log every ~0.5s
        let logEveryPolls = max(1, Int((0.5 / Self.meterIntervalSeconds).rounded()))
        if segmentTotalPolls % logEveryPolls == 0 {
            let ratio = segmentTotalPolls > 0 ? Float(segmentSpeechPolls) / Float(segmentTotalPolls) : 0
            print("[VAD] power=\(String(format: "%.1f", power))dB threshold=\(vadThresholdDb)dB speech=\(segmentHasSpeech) silence=\(segmentSilenceMs)ms elapsed=\(String(format: "%.1f", elapsed))s isSpeech=\(isSpeech) ratio=\(String(format: "%.0f", ratio * 100))%")
        }

        if isSpeech {
            segmentHasSpeech = true
            segmentSilenceMs = 0
            return
        }

        // Silence after speech
        if segmentHasSpeech {
            segmentSilenceMs += Int((Self.meterIntervalSeconds * 1000).rounded())
            if elapsed >= minSegmentSeconds && segmentSilenceMs >= vadSilenceMs {
                print("[VAD] Segment #\(seq) stopped: speech+silence threshold")
                stopCurrentSegment()
            }
        }
    }

    private func stopCurrentSegment() {
        segmentStopRequested = true
        finishCurrentSegment(discard: false)

        // Chain to next segment (engine keeps running, tap stays)
        if recording {
            do {
                try openNewSegmentFile()
                if vadEnabled {
                    startMetering()
                }
            } catch {
                print("[Recorder] next segment failed: \(error)")
                stop()
            }
        }
    }

    private func finishCurrentSegment(discard: Bool) {
        DispatchQueue.main.async { [weak self] in
            self?.meterTimer?.invalidate()
            self?.meterTimer = nil
        }

        audioLock.lock()
        segmentFile = nil  // close segment file
        audioLock.unlock()

        guard let url = currentSegmentURL else { return }
        currentSegmentURL = nil
        let currentSeq = seq
        let currentSessionID = sessionID

        // Compute segment-level RMS to filter out near-silent segments
        let segmentRMS = segmentSampleCount > 0
            ? Float(sqrt(segmentSumSquares / Double(segmentSampleCount)))
            : 0

        let speechRatio = segmentTotalPolls > 0
            ? Float(segmentSpeechPolls) / Float(segmentTotalPolls)
            : 0

        if discard || !segmentHasSpeech {
            print("[Recorder] Segment #\(currentSeq) discarded (no speech detected)")
            try? FileManager.default.removeItem(at: url)
        } else if segmentRMS < Self.minSegmentRMS {
            print("[Recorder] Segment #\(currentSeq) discarded (RMS \(String(format: "%.4f", segmentRMS)) < \(Self.minSegmentRMS), likely silence/noise)")
            try? FileManager.default.removeItem(at: url)
        } else if speechRatio < Self.minSpeechRatio {
            print("[Recorder] Segment #\(currentSeq) discarded (speech ratio \(String(format: "%.0f", speechRatio * 100))% < \(String(format: "%.0f", Self.minSpeechRatio * 100))%, likely transient noise)")
            try? FileManager.default.removeItem(at: url)
        } else {
            print("[Recorder] Segment #\(currentSeq) ready (RMS=\(String(format: "%.4f", segmentRMS)), speech=\(String(format: "%.0f", speechRatio * 100))%), sending to API")
            onSegmentReady?(url, currentSeq, currentSessionID)
        }
    }

    // MARK: - Audio Session

    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(
                .playAndRecord,
                mode: .voiceChat,
                options: [.defaultToSpeaker, .allowBluetoothHFP, .allowBluetoothA2DP]
            )
            try session.setPreferredSampleRate(48_000)
            try session.setPreferredIOBufferDuration(0.01)
            try configurePreferredInputRoute(session)
            try session.setActive(true, options: [])
            try maximizeInputGainIfPossible(session)
            logCurrentAudioRoute(session)
        } catch {
            throw AudioRecorderError.failedToConfigureAudioSession
        }
    }

    private func configurePreferredInputRoute(_ session: AVAudioSession) throws {
        guard let availableInputs = session.availableInputs else { return }
        guard let builtInMic = availableInputs.first(where: { $0.portType == .builtInMic }) else { return }

        try session.setPreferredInput(builtInMic)

        guard let dataSources = builtInMic.dataSources, !dataSources.isEmpty else { return }
        let preferred = dataSources.first(where: { $0.orientation == .front })
            ?? dataSources.first(where: { $0.orientation == .bottom })
            ?? dataSources.first(where: { $0.orientation == .back })
            ?? dataSources.first

        if let preferred {
            try builtInMic.setPreferredDataSource(preferred)
            print("🎙️ [Recorder] preferred mic data source: \(preferred.dataSourceName)")
        }
    }

    private func maximizeInputGainIfPossible(_ session: AVAudioSession) throws {
        guard session.isInputGainSettable else { return }
        let targetGain: Float = 1.0
        if abs(session.inputGain - targetGain) > 0.001 {
            try session.setInputGain(targetGain)
            print("🎙️ [Recorder] input gain boosted to \(targetGain)")
        }
    }

    private func logCurrentAudioRoute(_ session: AVAudioSession) {
        let inputs = session.currentRoute.inputs.map { "\($0.portType.rawValue):\($0.portName)" }.joined(separator: ", ")
        let outputs = session.currentRoute.outputs.map { "\($0.portType.rawValue):\($0.portName)" }.joined(separator: ", ")
        print("🎙️ [Recorder] audio route in=[\(inputs)] out=[\(outputs)]")
        print("🎙️ [Recorder] audio config sampleRate=\(session.sampleRate) ioBuffer=\(session.ioBufferDuration)s")
    }

    private func requestMicPermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }
}
