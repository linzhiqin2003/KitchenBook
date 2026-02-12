import Foundation
import SwiftUI

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var user: UserProfileResponse?

    // Form fields
    @Published var email = ""
    @Published var password = ""
    @Published var nickname = ""
    @Published var groqApiKey = ""
    @Published var isRegistering = false

    @AppStorage("apiBaseURL") private var userBaseURL: String = ""

    var apiBaseURL: String {
        let url = userBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        if !url.isEmpty { return url }
        return (Bundle.main.object(forInfoDictionaryKey: "MyWebAPIBaseURL") as? String) ?? "https://www.lzqqq.org"
    }

    init() {
        if KeychainService.load(.accessToken) != nil {
            isAuthenticated = true
            Task { await fetchProfile() }
        }
    }

    func login() {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Please enter email and password"
            return
        }
        isLoading = true
        errorMessage = nil

        Task {
            do {
                let body = LoginRequest(username: email, password: password)
                let data = try await postJSON(path: "/api/auth/login/", body: body)

                // SimpleJWT login returns { access, refresh } (no user object)
                struct JWTResponse: Decodable {
                    let access: String
                    let refresh: String
                }
                let tokens = try JSONDecoder().decode(JWTResponse.self, from: data)
                KeychainService.save(.accessToken, value: tokens.access)
                KeychainService.save(.refreshToken, value: tokens.refresh)

                // Fetch user profile
                await fetchProfile()
                isAuthenticated = true
            } catch let error as AuthError {
                errorMessage = error.message
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }

    func register() {
        guard !email.isEmpty, !password.isEmpty, !groqApiKey.isEmpty else {
            errorMessage = "请填写邮箱、密码和 API Key"
            return
        }
        isLoading = true
        errorMessage = nil

        Task {
            do {
                let body = RegisterRequest(
                    email: email,
                    password: password,
                    nickname: nickname,
                    groq_api_key: groqApiKey
                )
                let data = try await postJSON(path: "/api/auth/register/", body: body)
                let response = try JSONDecoder().decode(AuthTokenResponse.self, from: data)

                KeychainService.save(.accessToken, value: response.access)
                KeychainService.save(.refreshToken, value: response.refresh)
                user = response.user
                isAuthenticated = true
            } catch let error as AuthError {
                errorMessage = error.message
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }

    func logout() {
        KeychainService.delete(.accessToken)
        KeychainService.delete(.refreshToken)
        user = nil
        isAuthenticated = false
        email = ""
        password = ""
        nickname = ""
        groqApiKey = ""
    }

    /// Update Groq API Key via PATCH /api/auth/me/. Returns status message.
    func updateGroqKey(_ key: String) async -> String {
        guard let token = KeychainService.load(.accessToken) else {
            return "Not authenticated"
        }
        let urlString = apiBaseURL.hasSuffix("/") ? "\(apiBaseURL)api/auth/me/" : "\(apiBaseURL)/api/auth/me/"
        guard let url = URL(string: urlString) else { return "Invalid API URL" }
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONEncoder().encode(["groq_api_key": key])
        request.timeoutInterval = 30

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else { return "No response" }

            if http.statusCode == 200 {
                // Refresh user profile
                if let profile = try? JSONDecoder().decode(UserProfileResponse.self, from: data) {
                    user = profile
                }
                return "Updated successfully"
            } else {
                if let errResp = try? JSONDecoder().decode(APIErrorResponse.self, from: data) {
                    return errResp.groq_api_key?.joined(separator: ", ")
                        ?? errResp.detail
                        ?? "HTTP \(http.statusCode)"
                }
                return "HTTP \(http.statusCode)"
            }
        } catch {
            return error.localizedDescription
        }
    }

    func refreshAccessToken() async -> Bool {
        guard let refreshToken = KeychainService.load(.refreshToken) else {
            logout()
            return false
        }

        struct RefreshBody: Encodable { let refresh: String }
        do {
            let data = try await postJSON(
                path: "/api/auth/token/refresh/",
                body: RefreshBody(refresh: refreshToken)
            )
            let response = try JSONDecoder().decode(TokenRefreshResponse.self, from: data)
            KeychainService.save(.accessToken, value: response.access)
            if let newRefresh = response.refresh {
                KeychainService.save(.refreshToken, value: newRefresh)
            }
            return true
        } catch {
            logout()
            return false
        }
    }

    private func fetchProfile() async {
        guard let token = KeychainService.load(.accessToken) else { return }

        let urlString = apiBaseURL.hasSuffix("/") ? "\(apiBaseURL)api/auth/me/" : "\(apiBaseURL)/api/auth/me/"
        guard let url = URL(string: urlString) else { return }
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.timeoutInterval = 15

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else { return }

            if http.statusCode == 200 {
                user = try JSONDecoder().decode(UserProfileResponse.self, from: data)
                return
            }

            // Token expired → refresh and retry once
            if http.statusCode == 401 {
                let refreshed = await refreshAccessToken()
                if refreshed, let newToken = KeychainService.load(.accessToken) {
                    var retryReq = request
                    retryReq.setValue("Bearer \(newToken)", forHTTPHeaderField: "Authorization")
                    let (retryData, retryResp) = try await URLSession.shared.data(for: retryReq)
                    if let retryHttp = retryResp as? HTTPURLResponse, retryHttp.statusCode == 200 {
                        user = try JSONDecoder().decode(UserProfileResponse.self, from: retryData)
                    }
                }
            }
        } catch {
            print("Failed to fetch profile: \(error)")
        }
    }

    // MARK: - HTTP Helpers

    private enum AuthError: Error {
        case serverError(String)
        var message: String {
            switch self {
            case .serverError(let msg): return msg
            }
        }
    }

    private func postJSON<T: Encodable>(path: String, body: T) async throws -> Data {
        let baseStr = apiBaseURL.hasSuffix("/") ? apiBaseURL : "\(apiBaseURL)/"
        let pathStr = path.hasPrefix("/") ? String(path.dropFirst()) : path
        guard let url = URL(string: "\(baseStr)\(pathStr)") else {
            throw AuthError.serverError("Invalid API URL")
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)
        request.timeoutInterval = 30

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AuthError.serverError("No response")
        }

        if http.statusCode >= 400 {
            // Try to parse error response
            if let errResp = try? JSONDecoder().decode(APIErrorResponse.self, from: data) {
                let messages = [
                    errResp.detail,
                    errResp.email?.joined(separator: ", "),
                    errResp.password?.joined(separator: ", "),
                    errResp.groq_api_key?.joined(separator: ", "),
                ].compactMap { $0 }.joined(separator: "\n")
                throw AuthError.serverError(messages.isEmpty ? "HTTP \(http.statusCode)" : messages)
            }
            throw AuthError.serverError("HTTP \(http.statusCode)")
        }

        return data
    }
}
