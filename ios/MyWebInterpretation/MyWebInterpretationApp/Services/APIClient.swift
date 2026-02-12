import Foundation

enum APIError: LocalizedError {
    case invalidBaseURL(String)
    case unexpectedResponse
    case httpError(Int, String?)  // (statusCode, server error message)
    case unauthorized
    case groqKeyRevoked
    case rateLimited
    case insufficientCredits(balance: Int, required: Int)

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL:
            return "服务器地址无效，请在设置中检查"
        case .unexpectedResponse:
            return "服务器响应异常，请稍后重试"
        case .httpError(let code, let serverMsg):
            if let msg = serverMsg { return msg }
            switch code {
            case 400: return "请求有误，请重试"
            case 403: return "权限不足 (\(code))"
            case 500: return "服务器内部错误，请稍后重试"
            case 502, 503: return "服务器暂时不可用，请稍后重试"
            case 504: return "服务器响应超时，请重试"
            default: return "请求失败 (\(code))，请稍后重试"
            }
        case .unauthorized:
            return "登录已过期，请重新登录"
        case .groqKeyRevoked:
            return "API Key 已失效，请在设置中更新"
        case .rateLimited:
            return "请求过于频繁，请稍等几秒再试"
        case .insufficientCredits(let balance, let required):
            let balMin = balance / 60
            let reqMin = max(1, required / 60)
            return "余额不足：剩余 \(balMin) 分钟，需要 \(reqMin) 分钟"
        }
    }

    var isGroqKeyRevoked: Bool {
        if case .groqKeyRevoked = self { return true }
        return false
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
        targetLang: String,
        asrTier: String = "free",
        sessionId: String? = nil
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
        form.addField(name: "asr_tier", value: asrTier)
        if let sessionId, !sessionId.isEmpty {
            form.addField(name: "session_id", value: sessionId)
        }
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
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               json["key_revoked"] as? Bool == true {
                throw APIError.groqKeyRevoked
            }
            throw APIError.unauthorized
        }
        if http.statusCode == 402 {
            // Parse balance/required from response
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                let balance = json["balance_seconds"] as? Int ?? 0
                let required = json["required_seconds"] as? Int ?? 0
                throw APIError.insufficientCredits(balance: balance, required: required)
            }
            throw APIError.insufficientCredits(balance: 0, required: 0)
        }
        if http.statusCode == 429 {
            throw APIError.rateLimited
        }
        if http.statusCode >= 400 {
            let bodyStr = String(data: data, encoding: .utf8)
            print("[API] HTTP \(http.statusCode), body: \(bodyStr ?? "")")
            let serverMsg = Self.parseErrorMessage(from: data)
            throw APIError.httpError(http.statusCode, serverMsg)
        }

        return try JSONDecoder().decode(TranscribeTranslateResponse.self, from: data)
    }

    func refineTranscription(
        text: String,
        sourceLang: String,
        targetLang: String
    ) async throws -> RefineResponse {
        let baseStr = baseURL.absoluteString
        let urlStr = baseStr.hasSuffix("/") ? "\(baseStr)api/interpretation/refine/" : "\(baseStr)/api/interpretation/refine/"
        guard let endpoint = URL(string: urlStr) else {
            throw APIError.invalidBaseURL(baseStr)
        }

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let body: [String: String] = [
            "text": text,
            "source_lang": sourceLang,
            "target_lang": targetLang,
        ]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.unexpectedResponse
        }
        if http.statusCode == 401 {
            throw APIError.unauthorized
        }
        if http.statusCode >= 400 {
            print("[API] refine HTTP \(http.statusCode), body: \(String(data: data, encoding: .utf8) ?? "")")
            throw APIError.httpError(http.statusCode, Self.parseErrorMessage(from: data))
        }

        return try JSONDecoder().decode(RefineResponse.self, from: data)
    }

    func generateTitle(text: String) async throws -> String {
        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("interpretation")
            .appendingPathComponent("generate-title")
            .appendingPathComponent("")

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        if let accessToken {
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        }

        let body: [String: String] = ["text": String(text.prefix(500))]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode < 400 else {
            throw APIError.unexpectedResponse
        }

        struct TitleResponse: Decodable { let title: String }
        return try JSONDecoder().decode(TitleResponse.self, from: data).title
    }

    func refineText(text: String, lang: String) async throws -> String {
        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("interpretation")
            .appendingPathComponent("refine-text")
            .appendingPathComponent("")

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 60
        if let accessToken {
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        }

        let body: [String: String] = ["text": text, "lang": lang]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.unexpectedResponse
        }
        if http.statusCode >= 400 {
            throw APIError.httpError(http.statusCode, Self.parseErrorMessage(from: data))
        }

        struct RefineTextResponse: Decodable { let refined_text: String }
        return try JSONDecoder().decode(RefineTextResponse.self, from: data).refined_text
    }

    /// Refine a long text by splitting into chunks at sentence boundaries (~5000 words each).
    func refineTextChunked(text: String, lang: String) async throws -> String {
        let chunks = Self.splitAtSentenceBoundary(text: text, maxWords: 5000)
        if chunks.count <= 1 {
            return try await refineText(text: text, lang: lang)
        }
        // Process chunks concurrently
        return try await withThrowingTaskGroup(of: (Int, String).self) { group in
            for (i, chunk) in chunks.enumerated() {
                group.addTask {
                    let refined = try await self.refineText(text: chunk, lang: lang)
                    return (i, refined)
                }
            }
            var results = [(Int, String)]()
            for try await result in group {
                results.append(result)
            }
            return results.sorted(by: { $0.0 < $1.0 }).map(\.1).joined(separator: " ")
        }
    }

    /// Split text into chunks of approximately `maxWords` words, cutting at the nearest sentence boundary.
    static func splitAtSentenceBoundary(text: String, maxWords: Int) -> [String] {
        let words = text.split(separator: " ", omittingEmptySubsequences: true)
        guard words.count > maxWords else { return [text] }

        var chunks = [String]()
        var start = 0

        while start < words.count {
            var end = min(start + maxWords, words.count)
            if end < words.count {
                // Search backward from `end` for a sentence-ending punctuation
                var best = end
                for i in stride(from: end - 1, through: max(start, end - 500), by: -1) {
                    let word = words[i]
                    if let last = word.last, ".!?。！？".contains(last) {
                        best = i + 1
                        break
                    }
                }
                end = best
            }
            let chunk = words[start..<end].joined(separator: " ")
            chunks.append(chunk)
            start = end
        }
        return chunks
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
            throw APIError.httpError(http.statusCode, nil)
        }
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    /// Parse {"error": "..."} from server JSON response
    static func parseErrorMessage(from data: Data) -> String? {
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let msg = json["error"] as? String {
            return msg
        }
        return nil
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

// MARK: - User-friendly error messages

extension Error {
    /// Convert any error to a short, user-friendly Chinese message.
    var friendlyMessage: String {
        // Already friendly APIError
        if self is APIError {
            return localizedDescription
        }
        // URLSession network errors
        let nsError = self as NSError
        if nsError.domain == NSURLErrorDomain {
            switch nsError.code {
            case NSURLErrorNotConnectedToInternet:
                return "无网络连接，请检查网络"
            case NSURLErrorTimedOut:
                return "请求超时，请稍后重试"
            case NSURLErrorCannotConnectToHost, NSURLErrorCannotFindHost:
                return "无法连接服务器，请检查网络"
            case NSURLErrorNetworkConnectionLost:
                return "网络连接中断，请重试"
            case NSURLErrorSecureConnectionFailed:
                return "安全连接失败，请检查网络"
            default:
                return "网络错误，请稍后重试"
            }
        }
        // Fallback
        return "操作失败，请重试"
    }
}
