import Foundation

struct LocalInterpretationRecording: Identifiable, Codable, Sendable {
    let id: UUID
    let createdAt: Date
    let title: String
    let durationSeconds: TimeInterval
    let sourceLang: String
    let targetLang: String
    let transcription: String
    let translation: String
    let audioFileName: String?
}

