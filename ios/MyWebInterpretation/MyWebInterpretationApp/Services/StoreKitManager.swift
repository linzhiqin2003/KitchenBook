import Foundation
import StoreKit

@MainActor
final class StoreKitManager: ObservableObject {
    @Published var products: [Product] = []
    @Published var purchaseInProgress = false
    @Published var lastError: String?

    static let productIDs: Set<String> = [
        "org.lzqqq.interpretation.credits.60",
        "org.lzqqq.interpretation.credits.300",
        "org.lzqqq.interpretation.credits.600",
    ]

    /// Called after successful purchase verification with backend.
    var onPurchaseVerified: ((String) async -> Void)?

    private var transactionListener: Task<Void, Never>?

    init() {
        transactionListener = listenForTransactions()
        Task { await loadProducts() }
    }

    deinit {
        transactionListener?.cancel()
    }

    func loadProducts() async {
        do {
            let storeProducts = try await Product.products(for: Self.productIDs)
            products = storeProducts.sorted { $0.price < $1.price }
        } catch {
            print("[StoreKit] Failed to load products: \(error)")
            lastError = "Failed to load products"
        }
    }

    func purchase(_ product: Product) async -> Bool {
        purchaseInProgress = true
        lastError = nil
        defer { purchaseInProgress = false }

        do {
            let result = try await product.purchase()

            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
                // Get JWS representation to send to backend
                let jwsRepresentation = verification.jwsRepresentation

                // Verify with backend
                if let onPurchaseVerified {
                    await onPurchaseVerified(jwsRepresentation)
                }

                await transaction.finish()
                return true

            case .userCancelled:
                return false

            case .pending:
                lastError = "Purchase pending approval"
                return false

            @unknown default:
                lastError = "Unknown purchase result"
                return false
            }
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    private nonisolated func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified(_, let error):
            throw error
        case .verified(let safe):
            return safe
        }
    }

    private func listenForTransactions() -> Task<Void, Never> {
        Task.detached {
            for await result in Transaction.updates {
                do {
                    let transaction = try self.checkVerified(result)
                    // Finish any unfinished transactions
                    await transaction.finish()
                } catch {
                    print("[StoreKit] Transaction verification failed: \(error)")
                }
            }
        }
    }

    // Product display helpers
    static func creditHours(for productID: String) -> Int {
        switch productID {
        case "org.lzqqq.interpretation.credits.60": return 1
        case "org.lzqqq.interpretation.credits.300": return 5
        case "org.lzqqq.interpretation.credits.600": return 10
        default: return 0
        }
    }
}
