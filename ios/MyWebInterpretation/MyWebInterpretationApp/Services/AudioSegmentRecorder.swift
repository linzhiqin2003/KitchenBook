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
    var vadThresholdDb: Float = -35.0
    var vadSilenceMs: Int = 400
    var minSegmentSeconds: TimeInterval = 0.3
    var maxSegmentSeconds: TimeInterval = 5.0
    var onSegmentReady: ((URL, Int) -> Void)?
    var onPowerUpdate: ((Float) -> Void)?

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
    private static let minSegmentRMS: Float = 0.01
    private static let minSpeechRatio: Float = 0.15  // at least 15% of polls must detect speech

    // Dual-file writing: segment file + accumulated file
    private var segmentFile: AVAudioFile?
    private var accumulatedFile: AVAudioFile?
    private var accumulatedURL: URL?
    private var storedOutputSettings: [String: Any]?
    private let audioLock = NSLock()

    func start() async throws {
        print("🎙️ [Recorder] start() called, requesting mic permission...")
        let granted = await requestMicPermission()
        print("🎙️ [Recorder] mic permission granted=\(granted)")
        guard granted else { throw AudioRecorderError.microphonePermissionDenied }

        print("🎙️ [Recorder] configuring audio session...")
        try configureAudioSession()
        print("🎙️ [Recorder] audio session configured OK")

        let newEngine = AVAudioEngine()

        engine = newEngine
        recording = true
        seq = 0

        // Store output settings for reuse
        let inputFormat = newEngine.inputNode.outputFormat(forBus: 0)
        storedOutputSettings = [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: inputFormat.sampleRate,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        ]

        // Install tap once — runs for entire recording session
        installTap(node: newEngine.inputNode, format: inputFormat)

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
        audioLock.unlock()

        try? AVAudioSession.sharedInstance().setActive(false, options: [])
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

    // MARK: - Tap & File Management

    private func installTap(node: AVAudioInputNode, format: AVAudioFormat) {
        node.installTap(onBus: 0, bufferSize: 2048, format: format) { [weak self] buffer, _ in
            guard let self = self else { return }

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

    /// Must be called with audioLock held.
    private func startNewAccumulatedFileUnlocked() {
        guard let settings = storedOutputSettings else { return }
        let dir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        let url = dir.appendingPathComponent("accumulated-\(UUID().uuidString).m4a")
        accumulatedURL = url
        accumulatedFile = try? AVAudioFile(forWriting: url, settings: settings)
    }

    // MARK: - VAD Metering

    private func startMetering() {
        DispatchQueue.main.async { [weak self] in
            self?.meterTimer?.invalidate()
            self?.meterTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
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
        if Int(elapsed * 20) % 10 == 0 {
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
            segmentSilenceMs += 50
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
            onSegmentReady?(url, currentSeq)
        }
    }

    // MARK: - Audio Session

    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetoothA2DP])
            try session.setPreferredIOBufferDuration(0.02)
            try session.setActive(true, options: [])
        } catch {
            throw AudioRecorderError.failedToConfigureAudioSession
        }
    }

    private func requestMicPermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }
}
