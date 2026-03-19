import ReplayKit
import AVFoundation
import CoreMedia

final class SampleHandler: RPBroadcastSampleHandler {

    // MARK: - Configuration

    private let segmentDuration: TimeInterval = 4.0
    private let targetSampleRate: Double = 48000.0

    // MARK: - State

    private var segmentsDir: URL!
    private var currentFileHandle: FileHandle?
    private var currentFileURL: URL?
    private var segmentByteCount: Int = 0
    private var segmentSampleCount: Int = 0
    private var segmentIndex: Int = 0
    private var actualSampleRate: Double = 48000.0
    private var groupDefaults: UserDefaults?

    // MARK: - Lifecycle

    override func broadcastStarted(withSetupInfo setupInfo: [String: NSObject]?) {
        groupDefaults = UserDefaults(suiteName: BroadcastConstants.appGroupID)

        guard let dir = BroadcastConstants.segmentsDirectory else {
            finishBroadcastWithError(NSError(
                domain: "BroadcastExtension", code: 1,
                userInfo: [NSLocalizedDescriptionKey: "App Group not configured"]
            ))
            return
        }
        segmentsDir = dir

        // Create segments directory
        try? FileManager.default.createDirectory(at: segmentsDir, withIntermediateDirectories: true)

        // Clean up old segment files
        cleanupOldSegments()

        // Mark broadcasting active
        groupDefaults?.set(true, forKey: BroadcastConstants.isBroadcastingKey)
        groupDefaults?.set(0, forKey: BroadcastConstants.segmentCounterKey)
        groupDefaults?.synchronize()

        segmentIndex = 0
        startNewSegment()
    }

    override func broadcastPaused() {
        // Finalize current segment on pause
        finalizeCurrentSegment(notify: true)
    }

    override func broadcastResumed() {
        startNewSegment()
    }

    override func broadcastFinished() {
        finalizeCurrentSegment(notify: true)

        // Mark broadcasting stopped
        groupDefaults?.set(false, forKey: BroadcastConstants.isBroadcastingKey)
        groupDefaults?.synchronize()

        // Send stopped notification
        postDarwinNotification(BroadcastConstants.broadcastStoppedNotification)
    }

    // MARK: - Sample Processing

    override func processSampleBuffer(_ sampleBuffer: CMSampleBuffer,
                                      with sampleBufferType: RPSampleBufferType) {
        switch sampleBufferType {
        case .audioApp:
            appendAudioSample(sampleBuffer)
        case .audioMic, .video:
            break
        @unknown default:
            break
        }
    }

    private func appendAudioSample(_ sampleBuffer: CMSampleBuffer) {
        guard let fileHandle = currentFileHandle else { return }

        guard let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer),
              let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(formatDesc) else {
            return
        }

        // Capture actual sample rate from the first buffer
        if segmentSampleCount == 0 {
            actualSampleRate = asbd.pointee.mSampleRate
        }

        guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }

        let length = CMBlockBufferGetDataLength(blockBuffer)
        var data = Data(count: length)
        data.withUnsafeMutableBytes { ptr in
            guard let baseAddr = ptr.baseAddress else { return }
            CMBlockBufferCopyDataBytes(blockBuffer, atOffset: 0, dataLength: length, destination: baseAddr)
        }

        // Convert to mono 16-bit PCM if needed
        let monoData = convertToMono16bit(data: data, asbd: asbd.pointee)

        fileHandle.write(monoData)
        segmentByteCount += monoData.count
        segmentSampleCount += monoData.count / 2  // 16-bit = 2 bytes per sample

        // Check if segment duration reached
        let currentDuration = Double(segmentSampleCount) / actualSampleRate
        if currentDuration >= segmentDuration {
            finalizeCurrentSegment(notify: true)
            startNewSegment()
        }
    }

    // MARK: - Audio Conversion

    private func convertToMono16bit(data: Data, asbd: AudioStreamBasicDescription) -> Data {
        let channels = Int(asbd.mChannelsPerFrame)
        let bitsPerChannel = Int(asbd.mBitsPerChannel)

        // Already mono 16-bit PCM
        if channels == 1 && bitsPerChannel == 16 &&
           asbd.mFormatID == kAudioFormatLinearPCM {
            return data
        }

        // Handle 32-bit float PCM (common from ReplayKit)
        if asbd.mFormatID == kAudioFormatLinearPCM &&
           (asbd.mFormatFlags & kAudioFormatFlagIsFloat) != 0 &&
           bitsPerChannel == 32 {
            return convertFloat32ToMono16(data: data, channels: channels)
        }

        // Handle 16-bit stereo PCM → mono
        if asbd.mFormatID == kAudioFormatLinearPCM &&
           bitsPerChannel == 16 && channels > 1 {
            return convertStereo16ToMono16(data: data, channels: channels)
        }

        // Fallback: return as-is (may produce artifacts)
        return data
    }

    private func convertFloat32ToMono16(data: Data, channels: Int) -> Data {
        let floatCount = data.count / 4
        let framesCount = floatCount / channels

        var output = Data(capacity: framesCount * 2)

        data.withUnsafeBytes { rawPtr in
            guard let floatPtr = rawPtr.baseAddress?.assumingMemoryBound(to: Float.self) else { return }

            for frame in 0..<framesCount {
                // Average all channels to mono
                var sum: Float = 0
                for ch in 0..<channels {
                    sum += floatPtr[frame * channels + ch]
                }
                let mono = sum / Float(channels)

                // Clamp and convert to Int16
                let clamped = max(-1.0, min(1.0, mono))
                var sample = Int16(clamped * 32767.0)
                output.append(Data(bytes: &sample, count: 2))
            }
        }

        return output
    }

    private func convertStereo16ToMono16(data: Data, channels: Int) -> Data {
        let frameSize = channels * 2  // 16-bit per channel
        let frameCount = data.count / frameSize

        var output = Data(capacity: frameCount * 2)

        data.withUnsafeBytes { rawPtr in
            guard let ptr = rawPtr.baseAddress?.assumingMemoryBound(to: Int16.self) else { return }

            for frame in 0..<frameCount {
                var sum: Int32 = 0
                for ch in 0..<channels {
                    sum += Int32(ptr[frame * channels + ch])
                }
                var mono = Int16(sum / Int32(channels))
                output.append(Data(bytes: &mono, count: 2))
            }
        }

        return output
    }

    // MARK: - WAV File Management

    private func startNewSegment() {
        let fileName = String(format: "segment_%04d.wav", segmentIndex)
        let fileURL = segmentsDir.appendingPathComponent(fileName)
        currentFileURL = fileURL

        // Create file with placeholder WAV header
        FileManager.default.createFile(atPath: fileURL.path, contents: nil)

        guard let handle = try? FileHandle(forWritingTo: fileURL) else { return }
        currentFileHandle = handle

        // Write placeholder WAV header (44 bytes)
        let header = makeWAVHeader(dataSize: 0, sampleRate: UInt32(actualSampleRate))
        handle.write(header)

        segmentByteCount = 0
        segmentSampleCount = 0
    }

    private func finalizeCurrentSegment(notify: Bool) {
        guard let handle = currentFileHandle, let fileURL = currentFileURL else { return }

        // Update WAV header with actual data size
        handle.seek(toFileOffset: 0)
        let header = makeWAVHeader(dataSize: UInt32(segmentByteCount), sampleRate: UInt32(actualSampleRate))
        handle.write(header)
        handle.closeFile()

        currentFileHandle = nil
        currentFileURL = nil

        // Only notify if there's actual audio data
        guard segmentByteCount > 0 else {
            try? FileManager.default.removeItem(at: fileURL)
            return
        }

        segmentIndex += 1

        // Update counter in shared defaults
        groupDefaults?.set(segmentIndex, forKey: BroadcastConstants.segmentCounterKey)
        groupDefaults?.synchronize()

        if notify {
            postDarwinNotification(BroadcastConstants.segmentReadyNotification)
        }
    }

    private func makeWAVHeader(dataSize: UInt32, sampleRate: UInt32) -> Data {
        var header = Data(capacity: 44)

        let channels: UInt16 = 1
        let bitsPerSample: UInt16 = 16
        let byteRate = sampleRate * UInt32(channels) * UInt32(bitsPerSample / 8)
        let blockAlign = channels * (bitsPerSample / 8)
        let fileSize = dataSize + 36

        // RIFF chunk
        header.append(contentsOf: "RIFF".utf8)
        header.append(uint32LE: fileSize)
        header.append(contentsOf: "WAVE".utf8)

        // fmt sub-chunk
        header.append(contentsOf: "fmt ".utf8)
        header.append(uint32LE: 16)           // sub-chunk size
        header.append(uint16LE: 1)            // PCM format
        header.append(uint16LE: channels)
        header.append(uint32LE: sampleRate)
        header.append(uint32LE: byteRate)
        header.append(uint16LE: blockAlign)
        header.append(uint16LE: bitsPerSample)

        // data sub-chunk
        header.append(contentsOf: "data".utf8)
        header.append(uint32LE: dataSize)

        return header
    }

    // MARK: - Cleanup

    private func cleanupOldSegments() {
        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: segmentsDir, includingPropertiesForKeys: nil
        ) else { return }

        for file in contents where file.pathExtension == "wav" {
            try? FileManager.default.removeItem(at: file)
        }
    }

    // MARK: - Darwin Notifications

    private func postDarwinNotification(_ name: String) {
        let center = CFNotificationCenterGetDarwinNotifyCenter()
        CFNotificationCenterPostNotification(
            center,
            CFNotificationName(name as CFString),
            nil,
            nil,
            true
        )
    }
}

// MARK: - Data Helpers

private extension Data {
    mutating func append(uint32LE value: UInt32) {
        var v = value.littleEndian
        append(Data(bytes: &v, count: 4))
    }

    mutating func append(uint16LE value: UInt16) {
        var v = value.littleEndian
        append(Data(bytes: &v, count: 2))
    }
}
