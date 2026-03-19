import Foundation
import Speech

/// On-device speech recognition using Apple's SFSpeechRecognizer.
/// Used as the fast pipeline for free-tier users — instant, no network needed.
actor AppleSpeechService {
    static let shared = AppleSpeechService()

    private var isAuthorized = false

    func requestAuthorization() async -> Bool {
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                let granted = status == .authorized
                continuation.resume(returning: granted)
            }
        }
    }

    /// Transcribe an audio file using Apple's on-device speech recognizer.
    /// Returns the transcription text, or nil if recognition fails.
    func transcribe(fileURL: URL, locale: Locale) async -> String? {
        if !isAuthorized {
            isAuthorized = await requestAuthorization()
            guard isAuthorized else {
                print("[AppleSpeech] Not authorized")
                return nil
            }
        }

        guard let recognizer = SFSpeechRecognizer(locale: locale), recognizer.isAvailable else {
            print("[AppleSpeech] Recognizer unavailable for locale \(locale.identifier)")
            return nil
        }

        // Prefer on-device recognition for speed
        if recognizer.supportsOnDeviceRecognition {
            print("[AppleSpeech] Using on-device recognition for \(locale.identifier)")
        }

        let request = SFSpeechURLRecognitionRequest(url: fileURL)
        request.shouldReportPartialResults = false
        // Don't force on-device — let the system choose (prefers on-device when available,
        // falls back to server if local model isn't downloaded)
        request.requiresOnDeviceRecognition = false

        do {
            let result = try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<SFSpeechRecognitionResult, Error>) in
                recognizer.recognitionTask(with: request) { result, error in
                    if let error = error {
                        continuation.resume(throwing: error)
                        return
                    }
                    if let result = result, result.isFinal {
                        continuation.resume(returning: result)
                    }
                }
            }
            let text = result.bestTranscription.formattedString
            print("[AppleSpeech] Transcribed (\(text.count) chars): \(text.prefix(60))...")
            return text
        } catch {
            print("[AppleSpeech] Recognition error: \(error)")
            return nil
        }
    }

    /// Map source language code (e.g. "en", "zh") to a Locale for SFSpeechRecognizer.
    static func locale(for langCode: String) -> Locale {
        switch langCode.lowercased() {
        case "zh": return Locale(identifier: "zh-CN")
        case "en": return Locale(identifier: "en-US")
        case "ja": return Locale(identifier: "ja-JP")
        case "ko": return Locale(identifier: "ko-KR")
        case "fr": return Locale(identifier: "fr-FR")
        case "de": return Locale(identifier: "de-DE")
        case "es": return Locale(identifier: "es-ES")
        case "ru": return Locale(identifier: "ru-RU")
        case "ar": return Locale(identifier: "ar-SA")
        case "pt": return Locale(identifier: "pt-BR")
        case "it": return Locale(identifier: "it-IT")
        default: return Locale(identifier: langCode)
        }
    }
}
