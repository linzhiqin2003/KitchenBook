import SwiftUI
import StoreKit

struct CreditStoreView: View {
    @ObservedObject var vm: InterpretationViewModel
    let baseURLString: String
    @Environment(\.dismiss) private var dismiss
    @StateObject private var store = StoreKitManager()
    @State private var purchaseMessage: String?
    @State private var isPurchaseSuccess = false

    var body: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Current Balance")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            HStack(alignment: .firstTextBaseline, spacing: 4) {
                                Text("\(vm.creditBalance / 60)")
                                    .font(.system(size: 36, weight: .bold, design: .rounded))
                                Text("min")
                                    .font(.title3)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        Image(systemName: "clock.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(.purple.opacity(0.6))
                    }
                    .padding(.vertical, 8)
                }

                Section(header: Text("Buy Credits")) {
                    if store.products.isEmpty {
                        HStack {
                            Spacer()
                            ProgressView("Loading products...")
                            Spacer()
                        }
                        .padding(.vertical, 12)
                    } else {
                        ForEach(store.products, id: \.id) { product in
                            productRow(product)
                        }
                    }
                }

                if let msg = purchaseMessage {
                    Section {
                        Text(msg)
                            .font(.footnote)
                            .foregroundStyle(isPurchaseSuccess ? .green : .red)
                    }
                }

                if let err = store.lastError {
                    Section {
                        Text(err)
                            .font(.footnote)
                            .foregroundStyle(.red)
                    }
                }

                Section {
                    Text("Premium ASR uses Qwen3-ASR-Flash for higher accuracy. Credits are deducted based on audio duration.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Credits")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .onAppear {
                configurePurchaseCallback()
            }
        }
    }

    @ViewBuilder
    private func productRow(_ product: Product) -> some View {
        let hours = StoreKitManager.creditHours(for: product.id)
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("\(hours) \(hours == 1 ? "hour" : "hours")")
                    .font(.headline)
                Text(product.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button {
                Task {
                    purchaseMessage = nil
                    let success = await store.purchase(product)
                    if success && purchaseMessage == nil {
                        // Fallback: onPurchaseVerified should have set the message
                        purchaseMessage = "Purchase successful!"
                        isPurchaseSuccess = true
                    }
                }
            } label: {
                if store.purchaseInProgress {
                    ProgressView()
                        .frame(width: 70)
                } else {
                    Text(product.displayPrice)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundStyle(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.purple)
                        .clipShape(Capsule())
                }
            }
            .disabled(store.purchaseInProgress)
        }
        .padding(.vertical, 4)
    }

    private func configurePurchaseCallback() {
        store.onPurchaseVerified = { jwsRepresentation in
            print("[CreditStore] onPurchaseVerified called, JWS length=\(jwsRepresentation.count)")

            guard let token = KeychainService.load(.accessToken) else {
                print("[CreditStore] No access token in keychain")
                await MainActor.run {
                    purchaseMessage = "Not logged in, please login first"
                    isPurchaseSuccess = false
                }
                return
            }

            print("[CreditStore] Token found, verifying with backend: \(baseURLString)")

            do {
                let service = try CreditService(
                    baseURLString: baseURLString,
                    accessToken: token
                )
                let response = try await service.verifyPurchase(jwsTransaction: jwsRepresentation)
                print("[CreditStore] Backend response: status=\(response.status) balance=\(response.balance_seconds ?? -1) added=\(response.credits_added ?? -1)")
                await MainActor.run {
                    if let balance = response.balance_seconds {
                        vm.creditBalance = balance
                    }
                    if response.status == "duplicate" {
                        purchaseMessage = "Already processed"
                        isPurchaseSuccess = true
                    } else {
                        let addedMin = (response.credits_added ?? 0) / 60
                        if addedMin >= 60 {
                            purchaseMessage = "+\(addedMin / 60)h added!"
                        } else {
                            purchaseMessage = "+\(addedMin) min added!"
                        }
                        isPurchaseSuccess = true
                    }
                }
            } catch {
                print("[CreditStore] Verification error: \(error)")
                await MainActor.run {
                    purchaseMessage = "Verification failed: \(error.localizedDescription)"
                    isPurchaseSuccess = false
                }
            }
        }
    }
}
