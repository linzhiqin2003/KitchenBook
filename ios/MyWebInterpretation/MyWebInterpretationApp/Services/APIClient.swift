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
        case .httpError(let code, _):
            switch code {
            case 400: return "音频格式有误，请重试"
            case 403: return "未配置 Groq API Key，请在设置中添加"
            case 500: return "服务器内部错误，请稍后重试"
            case 502, 503: return "服务器暂时不可用，请稍后重试"
            case 504: return "服务器响应超时，请重试"
            default: return "请求失败 (\(code))，请稍后重试"
            }
        case .unauthorized:
            return "登录已过期，请重新登录"
        case .groqKeyRevoked:
            return "Groq API Key 已失效，请在设置中更新"
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
        asrTier: String = "free"
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
    private static func parseErrorMessage(from data: Data) -> String? {
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
