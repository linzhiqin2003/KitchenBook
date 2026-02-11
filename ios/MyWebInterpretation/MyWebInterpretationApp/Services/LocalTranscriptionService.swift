import AVFoundation
import Foundation
import Speech

@available(iOS 26, *)
final class LocalTranscriptionService {

    enum TranscriptionError: LocalizedError {
        case unsupportedLocale(String)
        case emptyResult

        var errorDescription: String? {
            switch self {
            case .unsupportedLocale(let id):
                return "Locale \(id) is not supported for offline transcription"
            case .emptyResult:
                return "Transcription returned empty result"
            }
        }
    }

    /// Map app source language codes to SpeechTranscriber-compatible locales.
    static func locale(for sourceLang: String) -> Locale? {
        let mapping: [String: String] = [
            "en": "en_US",
            "zh": "zh_CN",
            "yue": "yue_CN",
            "ja": "ja_JP",
            "ko": "ko_KR",
            "fr": "fr_FR",
            "de": "de_DE",
            "es": "es_ES",
            "pt": "pt_BR",
            "ru": "ru_RU",
            "ar": "ar_SA",
            "it": "it_IT",
            "th": "th_TH",
            "vi": "vi_VN",
            "id": "id_ID",
            "ms": "ms_MY",
            "tr": "tr_TR",
            "hi": "hi_IN",
            "nl": "nl_NL",
            "pl": "pl_PL",
            "sv": "sv_SE",
            "da": "da_DK",
            "fi": "fi_FI",
            "cs": "cs_CZ",
            "el": "el_GR",
            "hu": "hu_HU",
            "ro": "ro_RO",
            "fa": "fa_IR",
            "fil": "fil_PH",
            "mk": "mk_MK",
        ]
        guard let identifier = mapping[sourceLang] else { return nil }
        return Locale(identifier: identifier)
    }

    /// Transcribe an audio file using on-device SpeechAnalyzer.
    static func transcribe(fileURL: URL, locale: Locale) async throws -> String {
        let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
        let audioFile = try AVAudioFile(forReading: fileURL)

        // Start collecting results concurrently before feeding audio.
        async let transcriptionFuture: String = try transcriber.results
            .reduce("") { str, result in str + String(result.text.characters) }

        let analyzer = SpeechAnalyzer(modules: [transcriber])
        if let lastSample = try await analyzer.analyzeSequence(from: audioFile) {
            try await analyzer.finalizeAndFinish(through: lastSample)
        } else {
            await analyzer.cancelAndFinishNow()
        }

        let fullText: String = try await transcriptionFuture
        let trimmed = fullText.trimmingCharacters(in: CharacterSet.whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            throw TranscriptionError.emptyResult
        }
        return trimmed
    }
}
