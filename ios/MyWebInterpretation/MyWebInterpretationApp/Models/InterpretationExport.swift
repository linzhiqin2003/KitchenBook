import Foundation

struct InterpretationExportPayload: Encodable, Sendable {
    struct Segment: Encodable, Sendable {
        let id: String
        let seq: Int
        let created_at: String
        let transcription: String
        let translation: String
        let status: String
        let error_message: String?
    }

    let exported_at: String
    let source_lang: String
    let target_lang: String
    let api_base_url: String
    let segments: [Segment]
}

