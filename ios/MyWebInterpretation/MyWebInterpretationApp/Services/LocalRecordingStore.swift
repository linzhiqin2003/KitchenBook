import Foundation

enum LocalRecordingStoreError: LocalizedError {
    case documentsUnavailable
    case fileCopyFailed

    var errorDescription: String? {
        switch self {
        case .documentsUnavailable:
            return "Unable to access app documents directory"
        case .fileCopyFailed:
            return "Unable to save audio file locally"
        }
    }
}

enum LocalRecordingStore {
    private static let folderName = "InterpretationRecordings"
    private static let indexFileName = "recordings.json"

    static func loadRecordings() throws -> [LocalInterpretationRecording] {
        let index = try indexURL()
        guard FileManager.default.fileExists(atPath: index.path) else { return [] }
        let data = try Data(contentsOf: index)
        let decoded = try JSONDecoder().decode([LocalInterpretationRecording].self, from: data)
        return decoded.sorted(by: { $0.createdAt > $1.createdAt })
    }

    static func addRecording(
        createdAt: Date,
        title: String,
        durationSeconds: TimeInterval,
        sourceLang: String,
        targetLang: String,
        transcription: String,
        translation: String,
        audioTempURL: URL?
    ) throws -> LocalInterpretationRecording {
        var records = try loadRecordings()
        let id = UUID()

        let audioFileName: String?
        if let audioTempURL {
            audioFileName = try moveAudioFileToStore(recordingID: id, from: audioTempURL)
        } else {
            audioFileName = nil
        }

        let entry = LocalInterpretationRecording(
            id: id,
            createdAt: createdAt,
            title: title,
            durationSeconds: durationSeconds,
            sourceLang: sourceLang,
            targetLang: targetLang,
            transcription: transcription,
            translation: translation,
            audioFileName: audioFileName
        )

        records.insert(entry, at: 0)
        try saveRecordings(records)
        return entry
    }

    static func deleteRecording(id: UUID) throws {
        var records = try loadRecordings()
        guard let idx = records.firstIndex(where: { $0.id == id }) else { return }
        let entry = records.remove(at: idx)
        try saveRecordings(records)

        if let audioURL = audioURL(for: entry) {
            try? FileManager.default.removeItem(at: audioURL)
        }
    }

    static func audioURL(for entry: LocalInterpretationRecording) -> URL? {
        guard let fileName = entry.audioFileName else { return nil }
        do {
            return try recordingsDirectory().appendingPathComponent(fileName)
        } catch {
            return nil
        }
    }

    private static func saveRecordings(_ records: [LocalInterpretationRecording]) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(records)
        try data.write(to: indexURL(), options: [.atomic])
    }

    private static func recordingsDirectory() throws -> URL {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            throw LocalRecordingStoreError.documentsUnavailable
        }

        let dir = docs.appendingPathComponent(folderName, isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    private static func indexURL() throws -> URL {
        try recordingsDirectory().appendingPathComponent(indexFileName)
    }

    private static func moveAudioFileToStore(recordingID: UUID, from tempURL: URL) throws -> String {
        let ext = tempURL.pathExtension.isEmpty ? "m4a" : tempURL.pathExtension
        let fileName = "recording-\(recordingID.uuidString).\(ext)"
        let destination = try recordingsDirectory().appendingPathComponent(fileName)

        try? FileManager.default.removeItem(at: destination)
        do {
            try FileManager.default.moveItem(at: tempURL, to: destination)
        } catch {
            do {
                try FileManager.default.copyItem(at: tempURL, to: destination)
                try? FileManager.default.removeItem(at: tempURL)
            } catch {
                throw LocalRecordingStoreError.fileCopyFailed
            }
        }
        return fileName
    }
}

