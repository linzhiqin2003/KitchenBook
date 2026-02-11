import Foundation

struct LocalPipelineResult: Sendable {
    let transcription: String
    let translation: String
    let isOffline: Bool = true
}

/// Combines on-device SpeechAnalyzer transcription + Translation framework.
/// Requires iOS 26+ for both SpeechTranscriber and TranslationSession(installedSource:target:).
@available(iOS 26, *)
final class LocalPipelineService {

    enum PipelineError: LocalizedError {
        case unsupportedSourceLang(String)
        case unsupportedTargetLang(String)

        var errorDescription: String? {
            switch self {
            case .unsupportedSourceLang(let lang):
                return "Source language '\(lang)' not supported for offline transcription"
            case .unsupportedTargetLang(let lang):
                return "Target language '\(lang)' not supported for offline translation"
            }
        }
    }

    /// Check if the local pipeline can handle the given language pair.
    static func isAvailable(sourceLang: String, targetLang: String) -> Bool {
        guard LocalTranscriptionService.locale(for: sourceLang) != nil else { return false }
        guard LocalTranslationService.sourceLanguage(for: sourceLang) != nil else { return false }
        guard LocalTranslationService.targetLanguage(for: targetLang) != nil else { return false }
        return true
    }

    /// Transcribe audio file locally, then translate the result locally.
    static func transcribeAndTranslate(
        fileURL: URL,
        sourceLang: String,
        targetLang: String
    ) async throws -> LocalPipelineResult {
        // Resolve locales
        guard let asrLocale = LocalTranscriptionService.locale(for: sourceLang) else {
            throw PipelineError.unsupportedSourceLang(sourceLang)
        }
        guard let transSource = LocalTranslationService.sourceLanguage(for: sourceLang) else {
            throw PipelineError.unsupportedSourceLang(sourceLang)
        }
        guard let transTarget = LocalTranslationService.targetLanguage(for: targetLang) else {
            throw PipelineError.unsupportedTargetLang(targetLang)
        }

        // Step 1: Transcribe
        let transcription = try await LocalTranscriptionService.transcribe(
            fileURL: fileURL,
            locale: asrLocale
        )

        // Step 2: Translate (skip if source == target)
        let translation: String
        if transSource.minimalIdentifier == transTarget.minimalIdentifier {
            translation = transcription
        } else {
            translation = try await LocalTranslationService.translate(
                text: transcription,
                from: transSource,
                to: transTarget
            )
        }

        return LocalPipelineResult(
            transcription: transcription,
            translation: translation
        )
    }
}
