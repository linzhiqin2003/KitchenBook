import Foundation

enum APIError: LocalizedError {
    case invalidBaseURL(String)
    case unexpectedResponse
    case httpError(Int)
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL(let s):
            return "Invalid API base URL: \(s)"
        case .unexpectedResponse:
            return "Unexpected server response"
        case .httpError(let code):
            return "Server returned HTTP \(code)"
        case .unauthorized:
            return "Authentication expired, please login again"
        }
    }
}

struct APIClient: Sendable {
    let baseURL: URL
    let accessToken: String?

    init(baseURLString: String, accessToken: String? = nil) throws {
        guard let url = URL(string: baseURLString) else {
            throw APIError.invalidBaseURL(baseURLString)
        }
        self.baseURL = url
        self.accessToken = accessToken
    }

    func transcribeTranslate(
        fileURL: URL,
        sourceLang: String,
        targetLang: String
    ) async throws -> TranscribeTranslateResponse {
        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("interpretation")
            .appendingPathComponent("transcribe-translate")
            .appendingPathComponent("")

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.timeoutInterval = 30
        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var form = MultipartFormData(boundary: boundary)
        form.addField(name: "source_lang", value: sourceLang)
        form.addField(name: "target_lang", value: targetLang)
        try form.addFile(
            name: "file",
            fileURL: fileURL,
            filename: "segment-\(UUID().uuidString).\(fileURL.pathExtension.isEmpty ? "wav" : fileURL.pathExtension)",
            mimeType: fileURL.pathExtension.lowercased() == "m4a" ? "audio/mp4" : "audio/wav"
        )
        request.httpBody = form.finalize()

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw APIError.unexpectedResponse
        }
        if http.statusCode == 401 {
            throw APIError.unauthorized
        }
        if http.statusCode >= 400 {
            print("[API] HTTP \(http.statusCode), body: \(String(data: data, encoding: .utf8) ?? "")")
            throw APIError.httpError(http.statusCode)
        }

        return try JSONDecoder().decode(TranscribeTranslateResponse.self, from: data)
    }

    func health() async throws -> HealthResponse {
        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("interpretation")
            .appendingPathComponent("health")
            .appendingPathComponent("")

        let (data, response) = try await URLSession.shared.data(from: endpoint)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.unexpectedResponse
        }
        if http.statusCode >= 400 {
            throw APIError.httpError(http.statusCode)
        }
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }
}

struct MultipartFormData {
    private let boundary: String
    private var data = Data()

    init(boundary: String) {
        self.boundary = boundary
    }

    mutating func addField(name: String, value: String) {
        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n")
        append("\(value)\r\n")
    }

    mutating func addFile(name: String, fileURL: URL, filename: String, mimeType: String) throws {
        let fileData = try Data(contentsOf: fileURL)

        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n")
        append("Content-Type: \(mimeType)\r\n\r\n")
        data.append(fileData)
        append("\r\n")
    }

    mutating func finalize() -> Data {
        append("--\(boundary)--\r\n")
        return data
    }

    private mutating func append(_ string: String) {
        if let d = string.data(using: .utf8) {
            data.append(d)
        }
    }
}
