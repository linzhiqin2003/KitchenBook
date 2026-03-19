import Foundation

enum BroadcastConstants {
    static let appGroupID = "group.org.lzqqq.interpretation"

    // Darwin notification names
    static let segmentReadyNotification = "org.lzqqq.interpretation.broadcast.segmentReady"
    static let broadcastStoppedNotification = "org.lzqqq.interpretation.broadcast.stopped"

    // UserDefaults keys (in App Group)
    static let isBroadcastingKey = "isBroadcasting"
    static let segmentCounterKey = "broadcastSegmentCounter"

    // Shared container URL (nil if App Group not provisioned yet)
    static var containerURL: URL? {
        FileManager.default
            .containerURL(forSecurityApplicationGroupIdentifier: appGroupID)
    }

    // Shared directory for segment files
    static var segmentsDirectory: URL? {
        containerURL?.appendingPathComponent("BroadcastSegments", isDirectory: true)
    }
}
