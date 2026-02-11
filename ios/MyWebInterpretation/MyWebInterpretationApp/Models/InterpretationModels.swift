import Foundation

struct TranscribeTranslateResponse: Decodable, Sendable {
    let transcription: String
    let translation: String
    let source_lang: String?
    let target_lang: String?
}

struct SegmentResult: Identifiable, Sendable {
    enum Status: String, Sendable {
        case uploading
        case transcribed
        case translated
        case done
        case error
    }

    let id: UUID
    let seq: Int
    let createdAt: Date
    var transcription: String
    var translation: String
    var status: Status
    var errorMessage: String?
    var isFinal: Bool

    init(seq: Int) {
        self.id = UUID()
        self.seq = seq
        self.createdAt = Date()
        self.transcription = ""
        self.translation = ""
        self.status = .uploading
        self.errorMessage = nil
        self.isFinal = false
    }
}

struct HealthResponse: Decodable, Sendable {
    let status: String
    let api_key_configured: Bool
}

// MARK: - Language Data

struct LangOption: Identifiable, Hashable {
    let id: String
    let name: String
}

let allSourceLanguages: [LangOption] = [
    .init(id: "en", name: "English"),
    .init(id: "zh", name: "中文"),
    .init(id: "yue", name: "粤语"),
    .init(id: "ja", name: "日本語"),
    .init(id: "ko", name: "한국어"),
    .init(id: "fr", name: "Français"),
    .init(id: "de", name: "Deutsch"),
    .init(id: "es", name: "Español"),
    .init(id: "pt", name: "Português"),
    .init(id: "ru", name: "Русский"),
    .init(id: "ar", name: "العربية"),
    .init(id: "it", name: "Italiano"),
    .init(id: "th", name: "ไทย"),
    .init(id: "vi", name: "Tiếng Việt"),
    .init(id: "id", name: "Bahasa Indonesia"),
    .init(id: "ms", name: "Bahasa Melayu"),
    .init(id: "tr", name: "Türkçe"),
    .init(id: "hi", name: "हिन्दी"),
    .init(id: "nl", name: "Nederlands"),
    .init(id: "pl", name: "Polski"),
    .init(id: "sv", name: "Svenska"),
    .init(id: "da", name: "Dansk"),
    .init(id: "fi", name: "Suomi"),
    .init(id: "cs", name: "Čeština"),
    .init(id: "el", name: "Ελληνικά"),
    .init(id: "hu", name: "Magyar"),
    .init(id: "ro", name: "Română"),
    .init(id: "fa", name: "فارسی"),
    .init(id: "fil", name: "Filipino"),
    .init(id: "mk", name: "Македонски"),
]

let allTargetLanguages: [LangOption] = [
    .init(id: "Chinese", name: "中文"),
    .init(id: "English", name: "English"),
    .init(id: "Cantonese", name: "粤语"),
    .init(id: "Japanese", name: "日本語"),
    .init(id: "Korean", name: "한국어"),
    .init(id: "French", name: "Français"),
    .init(id: "German", name: "Deutsch"),
    .init(id: "Spanish", name: "Español"),
    .init(id: "Portuguese", name: "Português"),
    .init(id: "Russian", name: "Русский"),
    .init(id: "Arabic", name: "العربية"),
    .init(id: "Italian", name: "Italiano"),
    .init(id: "Thai", name: "ไทย"),
    .init(id: "Vietnamese", name: "Tiếng Việt"),
    .init(id: "Indonesian", name: "Bahasa Indonesia"),
    .init(id: "Malay", name: "Bahasa Melayu"),
    .init(id: "Turkish", name: "Türkçe"),
    .init(id: "Hindi", name: "हिन्दी"),
    .init(id: "Dutch", name: "Nederlands"),
    .init(id: "Polish", name: "Polski"),
    .init(id: "Swedish", name: "Svenska"),
    .init(id: "Danish", name: "Dansk"),
    .init(id: "Finnish", name: "Suomi"),
    .init(id: "Czech", name: "Čeština"),
    .init(id: "Greek", name: "Ελληνικά"),
    .init(id: "Hungarian", name: "Magyar"),
    .init(id: "Romanian", name: "Română"),
    .init(id: "Persian", name: "فارسی"),
    .init(id: "Filipino", name: "Filipino"),
    .init(id: "Macedonian", name: "Македонски"),
]

// MARK: - Auth Models

struct AuthTokenResponse: Decodable {
    let access: String
    let refresh: String
    let user: UserProfileResponse
}

struct UserProfileResponse: Decodable {
    let id: Int
    let email: String
    let nickname: String?
    let has_groq_key: Bool?
}

struct TokenRefreshResponse: Decodable {
    let access: String
    let refresh: String?
}

struct RegisterRequest: Encodable {
    let email: String
    let password: String
    let nickname: String
    let groq_api_key: String
}

struct LoginRequest: Encodable {
    let username: String
    let password: String
}

struct APIErrorResponse: Decodable {
    let detail: String?
    let email: [String]?
    let password: [String]?
    let groq_api_key: [String]?
}
