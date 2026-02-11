import Foundation
import Translation

/// On-device translation using Apple's Translation framework.
/// Uses `TranslationSession(installedSource:target:)` which requires iOS 26+.
@available(iOS 26, *)
final class LocalTranslationService {

    /// Map app target language names to Translation framework language identifiers.
    static func targetLanguage(for targetLang: String) -> Locale.Language? {
        let mapping: [String: String] = [
            "Chinese": "zh-Hans",
            "English": "en",
            "Cantonese": "zh-Hant",
            "Japanese": "ja",
            "Korean": "ko",
            "French": "fr",
            "German": "de",
            "Spanish": "es",
            "Portuguese": "pt",
            "Russian": "ru",
            "Arabic": "ar",
            "Italian": "it",
            "Thai": "th",
            "Vietnamese": "vi",
            "Indonesian": "id",
            "Malay": "ms",
            "Turkish": "tr",
            "Hindi": "hi",
            "Dutch": "nl",
            "Polish": "pl",
            "Swedish": "sv",
            "Danish": "da",
            "Finnish": "fi",
            "Czech": "cs",
            "Greek": "el",
            "Hungarian": "hu",
            "Romanian": "ro",
            "Persian": "fa",
            "Filipino": "fil",
            "Macedonian": "mk",
        ]
        guard let identifier = mapping[targetLang] else { return nil }
        return Locale.Language(identifier: identifier)
    }

    /// Map app source language codes to Translation framework language identifiers.
    static func sourceLanguage(for sourceLang: String) -> Locale.Language? {
        let mapping: [String: String] = [
            "en": "en",
            "zh": "zh-Hans",
            "yue": "zh-Hant",
            "ja": "ja",
            "ko": "ko",
            "fr": "fr",
            "de": "de",
            "es": "es",
            "pt": "pt",
            "ru": "ru",
            "ar": "ar",
            "it": "it",
            "th": "th",
            "vi": "vi",
            "id": "id",
            "ms": "ms",
            "tr": "tr",
            "hi": "hi",
            "nl": "nl",
            "pl": "pl",
            "sv": "sv",
            "da": "da",
            "fi": "fi",
            "cs": "cs",
            "el": "el",
            "hu": "hu",
            "ro": "ro",
            "fa": "fa",
            "fil": "fil",
            "mk": "mk",
        ]
        guard let identifier = mapping[sourceLang] else { return nil }
        return Locale.Language(identifier: identifier)
    }

    /// Translate text using on-device Translation framework (iOS 26+).
    static func translate(
        text: String,
        from source: Locale.Language,
        to target: Locale.Language
    ) async throws -> String {
        let session = TranslationSession(installedSource: source, target: target)
        let response = try await session.translate(text)
        return response.targetText
    }
}
