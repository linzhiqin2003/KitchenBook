import SwiftUI

struct AuthView: View {
    @ObservedObject var authVM: AuthViewModel

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            BackgroundOrbs()

            ScrollView {
                VStack(spacing: 28) {
                    // Logo area
                    VStack(spacing: 8) {
                        Image(systemName: "waveform.and.mic")
                            .font(.system(size: 48))
                            .foregroundStyle(.white.opacity(0.8))
                            .padding(.top, 60)

                        Text("留学宝")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundStyle(.white)

                        Text("实时转译")
                            .font(.subheadline)
                            .foregroundStyle(.white.opacity(0.4))
                    }

                    // Segmented picker
                    Picker("", selection: $authVM.isRegistering) {
                        Text("登录").tag(false)
                        Text("注册").tag(true)
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal, 40)

                    // Form
                    VStack(spacing: 16) {
                        AuthTextField(
                            icon: "envelope",
                            placeholder: "邮箱",
                            text: $authVM.email,
                            keyboardType: .emailAddress
                        )

                        AuthTextField(
                            icon: "lock",
                            placeholder: "密码",
                            text: $authVM.password,
                            isSecure: true
                        )

                        if authVM.isRegistering {
                            AuthTextField(
                                icon: "person",
                                placeholder: "昵称（选填）",
                                text: $authVM.nickname
                            )

                            AuthTextField(
                                icon: "key",
                                placeholder: "API Key",
                                text: $authVM.groqApiKey
                            )

                            Button {
                                if let url = URL(string: "https://console.groq.com/keys") {
                                    UIApplication.shared.open(url)
                                }
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "questionmark.circle")
                                        .font(.caption)
                                    Text("如何获取 API Key?")
                                        .font(.caption)
                                }
                                .foregroundStyle(.blue.opacity(0.8))
                            }
                        }
                    }
                    .padding(.horizontal, 24)

                    // Error message
                    if let error = authVM.errorMessage {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 24)
                    }

                    // Submit button
                    Button {
                        if authVM.isRegistering {
                            authVM.register()
                        } else {
                            authVM.login()
                        }
                    } label: {
                        Group {
                            if authVM.isLoading {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Text(authVM.isRegistering ? "注册" : "登录")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color.iosBlue)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                    }
                    .disabled(authVM.isLoading)
                    .padding(.horizontal, 24)

                    Spacer(minLength: 40)
                }
            }
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - Auth Text Field

struct AuthTextField: View {
    let icon: String
    let placeholder: String
    @Binding var text: String
    var isSecure: Bool = false
    var keyboardType: UIKeyboardType = .default

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 15))
                .foregroundStyle(.white.opacity(0.4))
                .frame(width: 20)

            if isSecure {
                SecureField(placeholder, text: $text)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
            } else {
                TextField(placeholder, text: $text)
                    .keyboardType(keyboardType)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .background(Color.iosCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(.white.opacity(0.08))
        )
        .foregroundStyle(.white)
    }
}
