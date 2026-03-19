import Foundation

final class BroadcastReceiver {

    var onSegmentReady: ((URL) -> Void)?
    var onBroadcastStopped: (() -> Void)?

    private var isListening = false
    private var lastProcessedIndex: Int = -1
    private var pollTimer: Timer?

    // MARK: - Public

    func startListening() {
        guard !isListening else { return }
        isListening = true
        lastProcessedIndex = -1

        // Darwin notifications (immediate delivery when app is in foreground)
        registerDarwinObserver(
            name: BroadcastConstants.segmentReadyNotification,
            callback: { [weak self] in self?.handleSegmentReady() }
        )

        registerDarwinObserver(
            name: BroadcastConstants.broadcastStoppedNotification,
            callback: { [weak self] in self?.handleBroadcastStopped() }
        )

        // Polling fallback: Darwin notifications are lost when app is suspended.
        // Poll every 1.5s to catch segments written while we were in background.
        DispatchQueue.main.async { [weak self] in
            self?.pollTimer?.invalidate()
            self?.pollTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
                self?.handleSegmentReady()
                // Also check if broadcast was stopped while we were suspended
                self?.checkBroadcastEnded()
            }
        }

        print("[BroadcastReceiver] Started listening (Darwin + polling)")
    }

    func stopListening() {
        guard isListening else { return }
        isListening = false

        pollTimer?.invalidate()
        pollTimer = nil

        let center = CFNotificationCenterGetDarwinNotifyCenter()
        CFNotificationCenterRemoveEveryObserver(center, Unmanaged.passUnretained(self).toOpaque())
        observers.removeAll()

        print("[BroadcastReceiver] Stopped listening")
    }

    func cleanupSegments() {
        guard let dir = BroadcastConstants.segmentsDirectory else { return }
        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: dir, includingPropertiesForKeys: nil
        ) else { return }

        for file in contents where file.pathExtension == "wav" {
            try? FileManager.default.removeItem(at: file)
        }
        print("[BroadcastReceiver] Cleaned up segment files")
    }

    deinit {
        pollTimer?.invalidate()
        if isListening {
            let center = CFNotificationCenterGetDarwinNotifyCenter()
            CFNotificationCenterRemoveEveryObserver(center, Unmanaged.passUnretained(self).toOpaque())
        }
    }

    // MARK: - Segment Processing

    private func handleSegmentReady() {
        guard let dir = BroadcastConstants.segmentsDirectory else { return }

        guard let contents = try? FileManager.default.contentsOfDirectory(
            at: dir, includingPropertiesForKeys: nil
        ) else { return }

        let segmentFiles = contents
            .filter { $0.pathExtension == "wav" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }

        for file in segmentFiles {
            // Extract index from filename: segment_0001.wav → 1
            let name = file.deletingPathExtension().lastPathComponent
            let parts = name.split(separator: "_")
            guard parts.count == 2, let index = Int(parts[1]) else { continue }

            if index > lastProcessedIndex {
                lastProcessedIndex = index
                let tmpURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent("broadcast_\(UUID().uuidString).wav")
                do {
                    try FileManager.default.copyItem(at: file, to: tmpURL)
                    try? FileManager.default.removeItem(at: file)
                    print("[BroadcastReceiver] Segment ready: \(file.lastPathComponent)")
                    onSegmentReady?(tmpURL)
                } catch {
                    print("[BroadcastReceiver] Failed to copy segment: \(error)")
                }
            }
        }
    }

    private func handleBroadcastStopped() {
        print("[BroadcastReceiver] Broadcast stopped (Darwin)")
        handleSegmentReady()
        onBroadcastStopped?()
    }

    /// Polling check: detect if Extension set isBroadcasting=false while we were suspended.
    private func checkBroadcastEnded() {
        let defaults = UserDefaults(suiteName: BroadcastConstants.appGroupID)
        let stillBroadcasting = defaults?.bool(forKey: BroadcastConstants.isBroadcastingKey) ?? false
        if !stillBroadcasting {
            print("[BroadcastReceiver] Broadcast ended (detected by poll)")
            handleSegmentReady()
            onBroadcastStopped?()
        }
    }

    // MARK: - Darwin Notification Registration

    private var observers: [DarwinObserver] = []

    private func registerDarwinObserver(name: String, callback: @escaping () -> Void) {
        let observer = DarwinObserver(callback: callback)
        observers.append(observer)

        let center = CFNotificationCenterGetDarwinNotifyCenter()
        let pointer = Unmanaged.passUnretained(observer).toOpaque()

        CFNotificationCenterAddObserver(
            center,
            pointer,
            { (_, observer, _, _, _) in
                guard let observer = observer else { return }
                let obj = Unmanaged<DarwinObserver>.fromOpaque(observer).takeUnretainedValue()
                obj.callback()
            },
            name as CFString,
            nil,
            .deliverImmediately
        )
    }
}

private final class DarwinObserver {
    let callback: () -> Void
    init(callback: @escaping () -> Void) {
        self.callback = callback
    }
}
