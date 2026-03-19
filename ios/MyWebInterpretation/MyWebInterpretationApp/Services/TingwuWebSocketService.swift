import AVFoundation
import Foundation

final class TingwuWebSocketService: @unchecked Sendable {
    var onTranscription: ((String, Bool, Int) -> Void)?  // (text, isFinal, seq)
    var onTranslation: ((String, String) -> Void)?       // (text, originalText)
    var onSpeechStart: (() -> Void)?
    var onError: ((String) -> Void)?
    var onDisconnect: (() -> Void)?
    var onPowerUpdate: ((Float) -> Void)?

    private(set) var isRunning = false
    private(set) var isPaused = false
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var engine: AVAudioEngine?
    private let targetSampleRate: Double = 16000

    private var pcmBuffer = Data()
    private let bufferLock = NSLock()
    private var sendTimer: Timer?

    func start(baseURL: String, accessToken: String?, sourceLang: String, targetLang: String) async throws {
        guard !isRunning else { return }

        // Build WebSocket URL
        var wsURL = baseURL
            .replacingOccurrences(of: "https://", with: "wss://")
            .replacingOccurrences(of: "http://", with: "ws://")
        if wsURL.hasSuffix("/") { wsURL.removeLast() }
        wsURL += "/ws/interpretation/"

        if let token = accessToken, !token.isEmpty {
            wsURL += "?token=\(token)"
        }

        guard let url = URL(string: wsURL) else {
            throw APIError.invalidBaseURL(wsURL)
        }

        // Configure audio session
        try configureAudioSession()

        // Connect WebSocket
        let session = URLSession(configuration: .default)
        urlSession = session
        let task = session.webSocketTask(with: url)
        webSocketTask = task
        task.resume()

        isRunning = true

        // Send start message
        let startMsg: [String: String] = [
            "type": "start",
            "provider": "tingwu",
            "source_lang": sourceLang,
            "target_lang": targetLang,
        ]
        let startData = try JSONSerialization.data(withJSONObject: startMsg)
        try await task.send(.string(String(data: startData, encoding: .utf8)!))

        // Start listening for messages
        listenForMessages()

        // Start audio capture
        try startAudioCapture()

        // Start periodic audio send on main thread (needs RunLoop)
        await MainActor.run {
            self.sendTimer = Timer.scheduledTimer(withTimeInterval: 0.2, repeats: true) { [weak self] _ in
                self?.sendBufferedAudio()
            }
        }
    }

    func stop() {
        guard isRunning else { return }
        isRunning = false
        isPaused = false

        DispatchQueue.main.async { [weak self] in
            self?.sendTimer?.invalidate()
            self?.sendTimer = nil
        }

        // Send remaining audio
        sendBufferedAudio()

        // Stop audio engine
        engine?.stop()
        engine?.inputNode.removeTap(onBus: 0)
        engine = nil

        // Send stop message and close WebSocket
        webSocketTask?.send(.string("{\"type\":\"stop\"}")) { _ in }
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        urlSession?.invalidateAndCancel()
        urlSession = nil

        try? AVAudioSession.sharedInstance().setActive(false, options: [])

        bufferLock.lock()
        pcmBuffer.removeAll()
        bufferLock.unlock()
    }

    func pause() {
        guard isRunning, !isPaused else { return }
        isPaused = true
        engine?.pause()
        DispatchQueue.main.async { [weak self] in
            self?.sendTimer?.invalidate()
            self?.sendTimer = nil
        }
        sendBufferedAudio()
        print("[Tingwu] paused")
    }

    func resume() {
        guard isRunning, isPaused else { return }
        isPaused = false
        do {
            try engine?.start()
        } catch {
            print("[Tingwu] resume engine failed: \(error)")
            return
        }
        DispatchQueue.main.async { [weak self] in
            self?.sendTimer = Timer.scheduledTimer(withTimeInterval: 0.2, repeats: true) { [weak self] _ in
                self?.sendBufferedAudio()
            }
        }
        print("[Tingwu] resumed")
    }

    // MARK: - Audio Capture

    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(
            .playAndRecord,
            mode: .voiceChat,
            options: [.defaultToSpeaker, .allowBluetoothHFP, .allowBluetoothA2DP]
        )
        try session.setPreferredSampleRate(48_000)
        try session.setPreferredIOBufferDuration(0.01)
        try session.setActive(true, options: [])
    }

    private func startAudioCapture() throws {
        let newEngine = AVAudioEngine()
        do {
            try newEngine.inputNode.setVoiceProcessingEnabled(true)
            newEngine.inputNode.isVoiceProcessingBypassed = false
            newEngine.inputNode.isVoiceProcessingAGCEnabled = true
        } catch {
            print("[Tingwu] voice processing unavailable: \(error)")
        }
        engine = newEngine

        let hwFormat = newEngine.inputNode.outputFormat(forBus: 0)
        let tapFormat: AVAudioFormat? = (hwFormat.sampleRate > 0 && hwFormat.channelCount > 0) ? hwFormat : nil
        let deviceRate = tapFormat?.sampleRate ?? AVAudioSession.sharedInstance().sampleRate

        newEngine.inputNode.installTap(onBus: 0, bufferSize: 1024, format: tapFormat) { [weak self] buffer, _ in
            guard let self = self, self.isRunning, !self.isPaused else { return }

            // Compute power for waveform visualization
            if let ch = buffer.floatChannelData?[0] {
                let n = Int(buffer.frameLength)
                var sum: Float = 0
                for i in 0..<n { sum += ch[i] * ch[i] }
                let power = 20 * log10(max(sqrt(sum / max(Float(n), 1)), 1e-10))
                self.onPowerUpdate?(power)
            }

            // Convert to 16kHz Int16 PCM and buffer
            let pcm = Self.convertToInt16PCM(buffer: buffer, fromRate: deviceRate, toRate: self.targetSampleRate)
            self.bufferLock.lock()
            self.pcmBuffer.append(pcm)
            self.bufferLock.unlock()
        }

        try newEngine.start()
    }

    private static func convertToInt16PCM(buffer: AVAudioPCMBuffer, fromRate: Double, toRate: Double) -> Data {
        guard let ch = buffer.floatChannelData?[0] else { return Data() }
        let frameCount = Int(buffer.frameLength)
        let ratio = toRate / fromRate
        let outputCount = Int(Double(frameCount) * ratio)

        var output = Data(capacity: outputCount * 2)
        for i in 0..<outputCount {
            let srcIdx = Double(i) / ratio
            let idx = Int(srcIdx)
            let frac = Float(srcIdx - Double(idx))
            let sample: Float
            if idx + 1 < frameCount {
                sample = ch[idx] * (1 - frac) + ch[idx + 1] * frac
            } else if idx < frameCount {
                sample = ch[idx]
            } else {
                sample = 0
            }
            var int16 = Int16(max(-1.0, min(1.0, sample)) * 32767)
            withUnsafeBytes(of: &int16) { output.append(contentsOf: $0) }
        }
        return output
    }

    private func sendBufferedAudio() {
        bufferLock.lock()
        guard !pcmBuffer.isEmpty else { bufferLock.unlock(); return }
        let data = pcmBuffer
        pcmBuffer.removeAll(keepingCapacity: true)
        bufferLock.unlock()

        guard isRunning, let task = webSocketTask else { return }
        task.send(.data(data)) { error in
            if let error = error { print("[Tingwu] send error: \(error)") }
        }
    }

    // MARK: - WebSocket Messages

    private func listenForMessages() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self, self.isRunning else { return }
            switch result {
            case .success(let msg):
                switch msg {
                case .string(let text): self.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) { self.handleMessage(text) }
                @unknown default: break
                }
                self.listenForMessages()
            case .failure(let error):
                print("[Tingwu] WebSocket error: \(error)")
                self.onDisconnect?()
            }
        }
    }

    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String else { return }

        switch type {
        case "transcription":
            let t = json["text"] as? String ?? ""
            let isFinal = json["is_final"] as? Bool ?? false
            let seq = json["seq"] as? Int ?? 0
            onTranscription?(t, isFinal, seq)
        case "translation":
            let t = json["translated"] as? String ?? ""
            let orig = json["original"] as? String ?? ""
            onTranslation?(t, orig)
        case "speech_start":
            onSpeechStart?()
        case "error":
            let msg = json["message"] as? String ?? "Unknown error"
            onError?(msg)
        default: break
        }
    }

    // MARK: - Language Mapping

    static func mapSourceLang(_ lang: String) -> String {
        switch lang.lowercased() {
        case "zh": return "cn"
        default: return lang
        }
    }

    static func mapTargetLang(_ lang: String) -> String {
        switch lang {
        case "Chinese": return "cn"
        case "English": return "en"
        case "Japanese": return "ja"
        case "Cantonese": return "yue"
        default: return lang.lowercased()
        }
    }

    static func isSupported(sourceLang: String, targetLang: String) -> Bool {
        let supportedSource = ["zh", "en", "ja", "yue"]
        let supportedTarget = ["Chinese", "English", "Japanese", "Cantonese"]
        return supportedSource.contains(sourceLang.lowercased()) && supportedTarget.contains(targetLang)
    }
}
