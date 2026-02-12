import Foundation

struct CreditBalanceResponse: Decodable {
    let balance_seconds: Int
}

struct VerifyPurchaseResponse: Decodable {
    let status: String
    let transaction_id: String?
    let product_id: String?
    let credits_added: Int?
    let balance_seconds: Int?
    let message: String?
}

struct CreditService {
    let baseURL: URL
    let accessToken: String

    init(baseURLString: String, accessToken: String) throws {
        guard let url = URL(string: baseURLString) else {
            throw APIError.invalidBaseURL(baseURLString)
        }
        self.baseURL = url
        self.accessToken = accessToken
    }

    func getBalance() async throws -> CreditBalanceResponse {
        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("credits")
            .appendingPathComponent("balance")
            .appendingPathComponent("")

        var request = URLRequest(url: endpoint)
        request.httpMethod = "GET"
        request.timeoutInterval = 15
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.unexpectedResponse
        }
        if http.statusCode == 401 {
            throw APIError.unauthorized
        }
        if http.statusCode >= 400 {
            throw APIError.httpError(http.statusCode, APIClient.parseErrorMessage(from: data))
        }
        return try JSONDecoder().decode(CreditBalanceResponse.self, from: data)
    }

    func verifyPurchase(jwsTransaction: String) async throws -> VerifyPurchaseResponse {
        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("credits")
            .appendingPathComponent("verify-purchase")
            .appendingPathComponent("")

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.timeoutInterval = 30
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["jws_transaction": jwsTransaction]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.unexpectedResponse
        }
        if http.statusCode == 401 {
            throw APIError.unauthorized
        }
        if http.statusCode >= 400 {
            throw APIError.httpError(http.statusCode, APIClient.parseErrorMessage(from: data))
        }
        return try JSONDecoder().decode(VerifyPurchaseResponse.self, from: data)
    }
}
