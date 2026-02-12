import SwiftUI
import Translation
import UniformTypeIdentifiers
import ReplayKit

// MARK: - Theme

extension Color {
    static let iosCard = Color(red: 28/255, green: 28/255, blue: 30/255)
    static let iosCard2 = Color(red: 44/255, green: 44/255, blue: 46/255)
    static let iosBlue = Color(red: 10/255, green: 132/255, blue: 255/255)
    static let iosRed = Color(red: 255/255, green: 69/255, blue: 58/255)
}

// MARK: - Speaker Colors

enum SpeakerColors {
    static let palette: [Color] = [
        .blue, .green, .orange, .purple, .pink, .cyan, .yellow, .mint,
    ]

    /// Extract speaker number from "speaker_1", "speaker_2" etc. and map to color.
    static func color(for speakerId: String?) -> Color? {
        guard let id = speakerId,
              let numStr = id.split(separator: "_").last,
              let num = Int(numStr), num >= 1 else { return nil }
        return palette[(num - 1) % palette.count]
    }

    /// Short label like "S1", "S2"
    static func shortLabel(for speakerId: String?) -> String? {
        guard let id = speakerId,
              let numStr = id.split(separator: "_").last,
              let num = Int(numStr), num >= 1 else { return nil }
        return "S\(num)"
    }
}

// MARK: - Speaker Badge

struct SpeakerBadge: View {
    let speakerId: String?

    var body: some View {
        if let label = SpeakerColors.shortLabel(for: speakerId),
           let color = SpeakerColors.color(for: speakerId) {
            Text(label)
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(color.opacity(0.7))
                .clipShape(Capsule())
        }
    }
}

// MARK: - Shimmer Effect

struct PendingFlowText: View {
    let text: String
    let font: Font
    let baseOpacity: Double

    var body: some View {
        Text(text)
            .font(font)
            .foregroundStyle(.white.opacity(baseOpacity))
            .overlay {
                // Use a stable TimelineView so the shimmer never resets when text changes
                TimelineView(.animation(minimumInterval: 1.0 / 60, paused: false)) { context in
                    GeometryReader { geo in
                        let w = geo.size.width
                        // Continuous 2.5s sweep cycle
                        let cycle = context.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: 2.5) / 2.5
                        let phase = cycle * 2.2 - 1.0  // range: -1.0 ... 1.2

                        LinearGradient(
                            stops: [
                                .init(color: .clear, location: 0),
                                .init(color: .white.opacity(0.35), location: 0.5),
                                .init(color: .clear, location: 1),
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                        .frame(width: w * 0.4)
                        .offset(x: phase * w)
                        .frame(width: w, alignment: .leading)
                        .clipped()
                    }
                    .mask {
                        Text(text).font(font)
                    }
                }
            }
    }
}

// MARK: - Background Orbs

struct BackgroundOrbs: View {
    @State private var animate = false

    var body: some View {
        ZStack {
            Circle()
                .fill(RadialGradient(
                    colors: [.blue.opacity(0.25), .clear],
                    center: .center, startRadius: 0, endRadius: 150
                ))
                .frame(width: 300, height: 300)
                .offset(x: animate ? -80 : -120, y: animate ? -220 : -180)

            Circle()
                .fill(RadialGradient(
                    colors: [.purple.opacity(0.2), .clear],
                    center: .center, startRadius: 0, endRadius: 120
                ))
                .frame(width: 250, height: 250)
                .offset(x: animate ? 100 : 80, y: animate ? 200 : 240)

            Circle()
                .fill(RadialGradient(
                    colors: [.indigo.opacity(0.15), .clear],
                    center: .center, startRadius: 0, endRadius: 100
                ))
                .frame(width: 200, height: 200)
                .offset(x: animate ? 60 : 40, y: animate ? -80 : -120)
        }
        .animation(.easeInOut(duration: 20).repeatForever(autoreverses: true), value: animate)
        .onAppear { animate = true }
    }
}

// MARK: - Language Picker Button

struct LangPickerButton: View {
    let label: String
    let options: [LangOption]
    @Binding var selection: String

    private var displayName: String {
        options.first(where: { $0.id == selection })?.name ?? selection
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.caption)
                .foregroundStyle(.white.opacity(0.4))

            Menu {
                ForEach(options) { lang in
                    Button {
                        selection = lang.id
                    } label: {
                        HStack {
                            Text(lang.name)
                            if selection == lang.id {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack {
                    Text(displayName)
                        .foregroundStyle(.white)
                    Spacer()
                    Image(systemName: "chevron.down")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.4))
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color.iosCard2)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }
}

// MARK: - Recording Pulse

struct PausedLabel: View {
    @State private var visible = true

    var body: some View {
        Text("暂停")
            .font(.caption2)
            .fontWeight(.medium)
            .foregroundStyle(.orange.opacity(visible ? 0.9 : 0.2))
            .animation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: visible)
            .onAppear { visible = false }
    }
}

struct PulseRing: View {
    @State private var scale: CGFloat = 1.0
    @State private var opacity: Double = 0.5

    var body: some View {
        Circle()
            .fill(Color.iosRed.opacity(0.25))
            .frame(width: 88, height: 88)
            .scaleEffect(scale)
            .opacity(opacity)
            .onAppear {
                withAnimation(.easeOut(duration: 1.5).repeatForever(autoreverses: false)) {
                    scale = 1.6
                    opacity = 0
                }
            }
    }
}

// MARK: - Waveform Visualizer

struct WaveformView: View {
    let levels: [CGFloat]
    let isActive: Bool

    var body: some View {
        HStack(alignment: .center, spacing: 2) {
            ForEach(0..<levels.count, id: \.self) { i in
                RoundedRectangle(cornerRadius: 1.5)
                    .fill(Color.iosRed.opacity(0.8))
                    .frame(width: 3, height: max(3, levels[i] * 56))
            }
        }
        .frame(height: 56)
        .animation(.linear(duration: 0.075), value: levels)
    }
}

// MARK: - Main View

struct ContentView: View {
    @ObservedObject var authVM: AuthViewModel
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @StateObject private var vm = InterpretationViewModel()
    @State private var showingSettings = false
    @State private var showingFilePicker = false
    @State private var showingLocalRecordings = false
    @State private var sharePayload: ShareSheetPayload?
    @State private var toastMessage: String?
    @State private var highlightedSegmentId: UUID? = nil
    @State private var displayMode: DisplayMode = .both
    @State private var layoutMode: LayoutMode = .text
    @State private var longPressProgress: CGFloat = 0
    @AppStorage("showSpeakerColors") private var showSpeakerColors: Bool = true
    @State private var showingCreditStore = false
    @State private var showingStopConfirmation = false

    enum DisplayMode: CaseIterable {
        case original
        case translation
        case both

        var title: String {
            switch self {
            case .original: return "Original"
            case .translation: return "Translation"
            case .both: return "Both"
            }
        }

        var icon: String {
            switch self {
            case .original: return "text.alignleft"
            case .translation: return "text.alignright"
            case .both: return "text.justify"
            }
        }

        var shortcutKey: KeyEquivalent {
            switch self {
            case .original: return "1"
            case .translation: return "2"
            case .both: return "3"
            }
        }
    }

    enum LayoutMode {
        case text      // 文本追加：连续段落
        case segments  // 逐列：每段独立卡片

        var icon: String {
            switch self {
            case .text: return "text.justify.leading"
            case .segments: return "list.bullet.rectangle"
            }
        }

        var title: String {
            switch self {
            case .text: return "Text"
            case .segments: return "Segments"
            }
        }
    }

    private var isPadLayout: Bool {
        UIDevice.current.userInterfaceIdiom == .pad || horizontalSizeClass == .regular
    }

    private var mainContentMaxWidth: CGFloat {
        isPadLayout ? 1120 : 760
    }

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            BackgroundOrbs()

            VStack(spacing: 0) {
                header
                scrollContent
                footer
            }
        }
        .preferredColorScheme(.dark)
        .onAppear {
            vm.authViewModel = authVM
            Task { await vm.fetchCreditBalance() }
        }
        .onChange(of: authVM.user?.email) { _ in
            // Profile loaded (e.g. after auto-login token refresh) → refresh balance
            Task { await vm.fetchCreditBalance() }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(apiBaseURL: vm.apiBaseURLBinding, authVM: authVM, vm: vm)
        }
        .sheet(isPresented: $showingCreditStore) {
            CreditStoreView(vm: vm, baseURLString: vm.apiBaseURL)
        }
        .sheet(isPresented: $showingLocalRecordings) {
            LocalRecordingsView(vm: vm)
        }
        .sheet(item: $sharePayload) { payload in
            ShareSheet(items: payload.items)
        }
        .fileImporter(
            isPresented: $showingFilePicker,
            allowedContentTypes: [.audio, .movie],
            allowsMultipleSelection: false
        ) { result in
            if case .success(let urls) = result, let url = urls.first {
                vm.uploadFile(url: url)
            }
        }
        .confirmationDialog("结束录制", isPresented: $showingStopConfirmation) {
            Button("保存并结束") {
                vm.stopAndSave()
            }
            Button("放弃录制", role: .destructive) {
                vm.stopAndDiscard()
            }
            Button("取消", role: .cancel) { }
        } message: {
            Text("是否保存本次录制内容？")
        }
        .translationSetup(vm: vm, sourceLang: vm.sourceLang, targetLang: vm.targetLang)
        .overlay(alignment: .bottom) {
            if let toastMessage {
                Text(toastMessage)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.95))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.black.opacity(0.65))
                    .clipShape(Capsule())
                    .padding(.bottom, 24)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
    }

    // MARK: - Header

    private var isSessionActive: Bool {
        vm.isRecording || vm.isPaused || vm.isBroadcasting
    }

    private var header: some View {
        HStack {
            Text("留学宝")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(.white)
                .onLongPressGesture { showingSettings = true }

            Spacer()

            if !isSessionActive {
                Text("实时转译")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(.white.opacity(0.45))

                Button {
                    showingSettings = true
                } label: {
                    Image(systemName: "gearshape")
                        .font(.system(size: 14))
                        .foregroundStyle(.white.opacity(0.5))
                }
                .keyboardShortcut(",", modifiers: [.command])
                .help("⌘, 设置")
                .padding(.leading, 10)

                Button {
                    showingLocalRecordings = true
                } label: {
                    Image(systemName: "list.bullet.rectangle")
                        .font(.system(size: 14))
                        .foregroundStyle(.white.opacity(0.5))
                }
                .keyboardShortcut("l", modifiers: [.command, .shift])
                .help("⇧⌘L 本地录音")
                .padding(.leading, 8)

                Button {
                    authVM.logout()
                } label: {
                    Image(systemName: "rectangle.portrait.and.arrow.right")
                        .font(.system(size: 14))
                        .foregroundStyle(.white.opacity(0.4))
                }
                .padding(.leading, 8)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
        .animation(.easeInOut(duration: 0.2), value: isSessionActive)
        .background(
            Rectangle()
                .fill(.ultraThinMaterial.opacity(0.3))
                .ignoresSafeArea(edges: .top)
        )
    }

    // MARK: - Scroll Content

    @ViewBuilder
    private var scrollContent: some View {
        if isPadLayout {
            VStack {
                ipadLayoutContent
                    .animation(.easeInOut(duration: 0.3), value: vm.isRecording)
                    .animation(.easeInOut(duration: 0.3), value: vm.isPaused)
                    .animation(.easeInOut(duration: 0.3), value: vm.isBroadcasting)
                    .frame(maxWidth: mainContentMaxWidth, alignment: .top)
                    .padding(.horizontal, 28)
                    .padding(.top, 22)
                    .padding(.bottom, 24)
                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        } else {
            ScrollView {
                phoneLayoutContent
                    .animation(.easeInOut(duration: 0.3), value: vm.isRecording)
                    .animation(.easeInOut(duration: 0.3), value: vm.isPaused)
                    .animation(.easeInOut(duration: 0.3), value: vm.isBroadcasting)
                    .frame(maxWidth: mainContentMaxWidth, alignment: .top)
                    .padding(.horizontal, 20)
                    .padding(.top, 16)
                    .padding(.bottom, 40)
            }
        }
    }

    private var phoneLayoutContent: some View {
        VStack(spacing: 24) {
            if !vm.isRecording && !vm.isPaused && !vm.isBroadcasting {
                languageSelectors
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
            inputArea

            if vm.segments.isEmpty {
                emptyState
            } else {
                resultsList
            }
        }
    }

    private var ipadLayoutContent: some View {
        VStack(spacing: 20) {
            if !vm.isRecording && !vm.isBroadcasting {
                languageSelectors
                    .frame(maxWidth: 820)
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }

            HStack(alignment: .top, spacing: 20) {
                inputArea
                    .frame(width: 360)
                    .frame(maxHeight: .infinity, alignment: .top)

                if vm.segments.isEmpty {
                    emptyResultsCard
                } else {
                    resultsList
                }
            }
            .frame(maxHeight: .infinity, alignment: .top)
        }
        .frame(maxHeight: .infinity, alignment: .top)
    }

    private var emptyResultsCard: some View {
        VStack {
            emptyState
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .strokeBorder(.white.opacity(0.08))
                )
        )
        .contextMenu {
            resultsContextMenu
        }
    }

    // MARK: - Language Selectors

    private var languageSelectors: some View {
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                LangPickerButton(label: "From", options: allSourceLanguages, selection: $vm.sourceLang)

                Image(systemName: "arrow.right")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.25))
                    .padding(.top, 22)

                LangPickerButton(label: "To", options: allTargetLanguages, selection: $vm.targetLang)
            }

            // Current mode indicator
            asrModeIndicator
        }
    }

    private var asrModeIndicator: some View {
        HStack(spacing: 8) {
            if vm.creditBalance > 0 {
                // Has credits: show mode toggle
                HStack(spacing: 0) {
                    modePill(title: "免费", icon: "bolt.fill", isSelected: vm.asrTier == "free") {
                        vm.asrTier = "free"
                    }
                    modePill(title: "高级", icon: "sparkles", isPremium: true, isSelected: vm.asrTier == "premium") {
                        vm.asrTier = "premium"
                    }
                }
                .background(.white.opacity(0.06))
                .clipShape(Capsule())

                if vm.asrTier == "premium" {
                    Text("\(vm.creditBalance / 60) min")
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.white.opacity(0.4))

                    Button { showingCreditStore = true } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.caption)
                            .foregroundStyle(.purple.opacity(0.7))
                    }

                    if vm.speakerEnabled {
                        HStack(spacing: 3) {
                            Image(systemName: "person.2.fill")
                                .font(.caption2)
                            Text("人声识别")
                                .font(.caption)
                        }
                        .foregroundStyle(.white.opacity(0.35))
                    }
                }
            } else {
                // No credits: free mode + upgrade entry
                HStack(spacing: 4) {
                    Image(systemName: "bolt.fill")
                        .font(.caption2)
                    Text("免费模式")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .foregroundStyle(.white.opacity(0.4))

                Button { showingCreditStore = true } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "sparkles")
                            .font(.caption2)
                        Text("升级")
                            .font(.caption)
                            .fontWeight(.medium)
                    }
                    .foregroundStyle(.purple)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(.purple.opacity(0.15))
                    .clipShape(Capsule())
                }
            }
        }
    }

    private func modePill(title: String, icon: String, isPremium: Bool = false, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button {
            withAnimation(.easeInOut(duration: 0.2)) { action() }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: icon).font(.caption2)
                Text(title).font(.caption).fontWeight(.medium)
            }
            .foregroundStyle(isSelected ? .white.opacity(0.9) : .white.opacity(0.3))
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(isSelected ? (isPremium ? Color.purple.opacity(0.3) : .white.opacity(0.1)) : .clear)
            .clipShape(Capsule())
        }
    }

    // MARK: - Input Area

    private var isPremiumNoCredits: Bool {
        vm.asrTier == "premium" && vm.creditBalance <= 0 && !vm.isRecording && !vm.isPaused && !vm.isBroadcasting
    }

    private var isActiveRecording: Bool {
        vm.isRecording && !vm.isPaused
    }

    private var recordingButtonColor: Color {
        if vm.isPaused { return .orange }
        if vm.isRecording { return Color.iosRed }
        return .white.opacity(0.1)
    }

    private var recordingButtonBorderColor: Color {
        if vm.isPaused { return .orange.opacity(0.5) }
        if vm.isRecording { return Color.iosRed.opacity(0.5) }
        return .white.opacity(0.2)
    }

    private var inputArea: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 24)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 24)
                        .strokeBorder(.white.opacity(0.08))
                )

            VStack(spacing: 14) {
                if isPremiumNoCredits {
                    // No credits prompt
                    VStack(spacing: 12) {
                        Image(systemName: "clock.badge.exclamationmark")
                            .font(.system(size: 36))
                            .foregroundStyle(.white.opacity(0.2))

                        Text("额度已用完")
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundStyle(.white.opacity(0.6))

                        Text("购买额度继续使用，或切换到免费模式")
                            .font(.caption)
                            .foregroundStyle(.white.opacity(0.3))
                            .multilineTextAlignment(.center)

                        HStack(spacing: 12) {
                            Button {
                                showingCreditStore = true
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.caption)
                                    Text("购买额度")
                                        .font(.caption)
                                        .fontWeight(.medium)
                                }
                                .foregroundStyle(.white)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(Color.purple.opacity(0.6))
                                .clipShape(Capsule())
                            }

                            Button {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    vm.asrTier = "free"
                                }
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "bolt.fill")
                                        .font(.caption)
                                    Text("免费模式")
                                        .font(.caption)
                                        .fontWeight(.medium)
                                }
                                .foregroundStyle(.white.opacity(0.7))
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(.white.opacity(0.08))
                                .clipShape(Capsule())
                            }
                        }
                        .padding(.top, 4)
                    }
                } else if vm.isBroadcasting {
                    // Broadcasting system audio state
                    VStack(spacing: 12) {
                        ZStack {
                            PulseRing()

                            Circle()
                                .fill(Color.purple.opacity(0.3))
                                .frame(width: 64, height: 64)
                                .overlay(
                                    Circle().strokeBorder(Color.purple.opacity(0.5), lineWidth: 2)
                                )
                                .shadow(color: .purple.opacity(0.35), radius: 16)

                            Image(systemName: "speaker.wave.3.fill")
                                .font(.title2)
                                .foregroundStyle(.white)
                        }

                        Text("正在监听系统音频")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundStyle(.purple.opacity(0.9))

                        Button {
                            vm.stopBroadcastListening()
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "stop.fill")
                                    .font(.caption)
                                Text("停止")
                                    .font(.caption)
                                    .fontWeight(.medium)
                            }
                            .foregroundStyle(.white)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 8)
                            .background(Color.purple.opacity(0.5))
                            .clipShape(Capsule())
                        }
                    }
                } else {
                    // Normal recording controls
                    ZStack {
                        // Waveform behind the button (only visible when actively recording)
                        if isActiveRecording {
                            WaveformView(levels: vm.waveformLevels, isActive: true)
                        }

                        if isActiveRecording {
                            PulseRing()
                        }

                        // Main recording button — tap to start/pause/resume, long-press to stop
                        ZStack {
                            Circle()
                                .fill(recordingButtonColor)
                                .frame(width: 64, height: 64)
                                .overlay(
                                    Circle().strokeBorder(
                                        recordingButtonBorderColor,
                                        lineWidth: 2
                                    )
                                )
                                .shadow(color: isActiveRecording ? Color.iosRed.opacity(0.35) : (vm.isPaused ? .orange.opacity(0.25) : .clear), radius: 16)

                            // Long press stop ring — track always visible when recording/paused
                            if vm.isRecording || vm.isPaused {
                                Circle()
                                    .stroke(Color.white.opacity(0.15), lineWidth: 3.5)
                                    .frame(width: 76, height: 76)

                                Circle()
                                    .trim(from: 0, to: longPressProgress)
                                    .stroke(
                                        Color.white,
                                        style: StrokeStyle(lineWidth: 3.5, lineCap: .round)
                                    )
                                    .frame(width: 76, height: 76)
                                    .rotationEffect(.degrees(-90))
                            }

                            if vm.isPaused {
                                Image(systemName: "play.fill")
                                    .font(.title2)
                                    .foregroundStyle(.white)
                            } else if vm.isRecording {
                                Image(systemName: "pause.fill")
                                    .font(.title2)
                                    .foregroundStyle(.white)
                            } else {
                                Image(systemName: "mic.fill")
                                    .font(.title2)
                                    .foregroundStyle(.white)
                            }
                        }
                        .contentShape(Circle())
                        .onTapGesture {
                            if vm.isRecording || vm.isPaused {
                                vm.togglePause()
                            } else {
                                vm.start()
                            }
                        }
                        .onLongPressGesture(minimumDuration: 0.6, pressing: { isPressing in
                            if vm.isRecording || vm.isPaused {
                                withAnimation(isPressing ? .linear(duration: 0.6) : .easeOut(duration: 0.15)) {
                                    longPressProgress = isPressing ? 1.0 : 0
                                }
                            }
                        }) {
                            if vm.isRecording || vm.isPaused {
                                UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
                                withAnimation(.easeOut(duration: 0.2)) {
                                    longPressProgress = 0
                                }
                                showingStopConfirmation = true
                            }
                        }

                        // Upload button (hidden when recording or paused)
                        if !vm.isRecording && !vm.isPaused {
                            Button { showingFilePicker = true } label: {
                                ZStack {
                                    Circle()
                                        .fill(.white.opacity(0.08))
                                        .frame(width: 30, height: 30)
                                        .overlay(Circle().strokeBorder(.white.opacity(0.12)))

                                    Image(systemName: "paperclip")
                                        .font(.system(size: 13))
                                        .foregroundStyle(.white.opacity(0.5))
                                }
                            }
                            .keyboardShortcut("u", modifiers: [.command])
                            .help("⌘U 上传音频")
                            .offset(x: 32, y: 24)
                        }

                        // Broadcast button (hidden when recording or paused)
                        if !vm.isRecording && !vm.isPaused {
                            Button {
                                BroadcastPickerTrigger.show(
                                    preferredExtension: broadcastExtensionBundleID
                                )
                                // Start listening for segments from the Extension
                                vm.startBroadcastListening()
                            } label: {
                                ZStack {
                                    Circle()
                                        .fill(.white.opacity(0.08))
                                        .frame(width: 30, height: 30)
                                        .overlay(Circle().strokeBorder(.white.opacity(0.12)))

                                    Image(systemName: "speaker.wave.2.fill")
                                        .font(.system(size: 11))
                                        .foregroundStyle(.purple.opacity(0.7))
                                }
                            }
                            .offset(x: -32, y: 24)
                        }
                    }

                    if vm.isRecording || vm.isPaused {
                        HStack(spacing: 6) {
                            Text(String(format: "%02d:%02d", vm.recordingSeconds / 60, vm.recordingSeconds % 60))
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(vm.isPaused ? .orange.opacity(0.9) : Color.iosRed.opacity(0.9))

                            if vm.isPaused {
                                PausedLabel()
                            }
                        }

                        Text("长按停止")
                            .font(.caption2)
                            .foregroundStyle(.white.opacity(0.25))
                    }
                }

                if let err = vm.lastError {
                    Text(err)
                        .font(.caption2)
                        .foregroundStyle(Color.iosRed)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            }
            .padding(.vertical, 28)
        }
        .frame(minHeight: isPadLayout ? 220 : 150)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 14) {
            Image(systemName: "waveform.and.mic")
                .font(.system(size: 40))
                .foregroundStyle(.white.opacity(0.12))

            Text("录音或上传音频文件，自动转录并翻译")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.3))

            Text("语音自动检测，停顿时自动切分")
                .font(.caption)
                .foregroundStyle(.white.opacity(0.18))
        }
        .padding(.top, 48)
    }

    // MARK: - Results

    // Final (slow pipeline confirmed) text
    private var finalTranscription: String {
        vm.segments.filter { $0.isFinal && !$0.transcription.isEmpty }
            .map { $0.transcription }.joined(separator: " ")
    }
    private var finalTranslation: String {
        vm.segments.filter { $0.isFinal && !$0.translation.isEmpty }
            .map { $0.translation }.joined(separator: " ")
    }

    // Pending (fast pipeline preliminary) text
    private var pendingTranscription: String {
        vm.segments.filter { !$0.isFinal && !$0.transcription.isEmpty }
            .map { $0.transcription }.joined(separator: " ")
    }
    private var pendingTranslation: String {
        vm.segments.filter { !$0.isFinal && !$0.translation.isEmpty }
            .map { $0.translation }.joined(separator: " ")
    }

    // Combined text for export/copy (final + pending)
    private var combinedTranscription: String {
        vm.segments.compactMap { $0.transcription.isEmpty ? nil : $0.transcription }
            .joined(separator: " ")
    }
    private var combinedTranslation: String {
        vm.segments.compactMap { $0.translation.isEmpty ? nil : $0.translation }
            .joined(separator: " ")
    }

    private var hasPending: Bool {
        vm.segments.contains { $0.status == .uploading || ($0.status != .done && $0.status != .error) }
    }

    private var displaySegments: [SegmentResult] {
        vm.segments
            .filter { !$0.transcription.isEmpty || !$0.translation.isEmpty }
    }

    private var resultsList: some View {
        VStack(spacing: 0) {
            HStack {
                Menu {
                    ForEach(DisplayMode.allCases, id: \.self) { mode in
                        Button {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                displayMode = mode
                            }
                        } label: {
                            Label(mode.title, systemImage: mode.icon)
                        }
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: displayMode.icon)
                            .font(.caption2)
                        Text(displayMode.title)
                            .font(.caption2)
                            .fontWeight(.medium)
                        Image(systemName: "chevron.down")
                            .font(.caption2)
                    }
                    .foregroundStyle(.white.opacity(0.75))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(.white.opacity(0.08))
                    .clipShape(Capsule())
                }
                Spacer()

                // Layout mode toggle
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        layoutMode = layoutMode == .text ? .segments : .text
                    }
                } label: {
                    Image(systemName: layoutMode.icon)
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.6))
                        .padding(7)
                        .background(.white.opacity(0.08))
                        .clipShape(Circle())
                }
                .keyboardShortcut("l", modifiers: [.command])
                .help("⌘L 切换文本/分段布局")
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            .padding(.bottom, 8)

            // Content columns
            resultsContent
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
                .contentShape(Rectangle())
                .simultaneousGesture(displayModeSwipeGesture)

            Rectangle()
                .fill(.white.opacity(0.06))
                .frame(height: 1)

            // Stats + mode indicator
            HStack {
                Text("\(combinedTranscription.split(separator: " ").count) words")
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.2))

                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: vm.asrTier == "premium" ? "sparkles" : "bolt.fill")
                        .font(.caption2)
                    Text(vm.asrTier == "premium" ? "高级" : "免费")
                        .font(.caption2)
                }
                .foregroundStyle(.white.opacity(0.25))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .strokeBorder(.white.opacity(0.08))
                )
        )
        .contextMenu {
            resultsContextMenu
        }
    }

    @ViewBuilder
    private var resultsContent: some View {
        if layoutMode == .text {
            resultsFlowView
        } else {
            resultsSegmentListView
        }
    }

    // MARK: - Text Flow Layout (文本追加)

    @ViewBuilder
    private var resultsFlowView: some View {
        let maxH: CGFloat = isPadLayout
            ? (displayMode == .both ? 520 : 650)
            : (displayMode == .both ? 240 : 360)

        switch displayMode {
        case .original:
            ScrollView {
                segmentFlowColumn(keyPath: \.transcription, isFinalOpacity: 0.9, pendingOpacity: 0.35)
            }
            .frame(maxHeight: maxH)

        case .translation:
            ScrollView {
                segmentFlowColumn(keyPath: \.translation, isFinalOpacity: 0.65, pendingOpacity: 0.25)
            }
            .frame(maxHeight: maxH)

        case .both:
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Original")
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.3))
                    ScrollView {
                        segmentFlowColumn(keyPath: \.transcription, isFinalOpacity: 0.9, pendingOpacity: 0.35)
                    }
                    .frame(maxHeight: maxH)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Rectangle()
                    .fill(.white.opacity(0.06))
                    .frame(width: 1)

                VStack(alignment: .leading, spacing: 6) {
                    Text("Translation")
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.3))
                    ScrollView {
                        segmentFlowColumn(keyPath: \.translation, isFinalOpacity: 0.65, pendingOpacity: 0.25)
                    }
                    .frame(maxHeight: maxH)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    // MARK: - Segment List Layout (逐列)

    @ViewBuilder
    private var resultsSegmentListView: some View {
        let maxH: CGFloat = isPadLayout ? 650 : 360
        let isLoading: (SegmentResult) -> Bool = { $0.status == .uploading || $0.status == .transcribed || $0.status == .translated }
        let segs = vm.segments.filter { seg in
            switch displayMode {
            case .original: return !seg.transcription.isEmpty || isLoading(seg)
            case .translation: return !seg.translation.isEmpty || isLoading(seg)
            case .both: return !seg.transcription.isEmpty || !seg.translation.isEmpty || isLoading(seg)
            }
        }

        ScrollView {
            LazyVStack(spacing: 8) {
                ForEach(segs) { seg in
                    segmentCard(seg)
                }
            }
        }
        .frame(maxHeight: maxH)
    }

    private static let segmentTimeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f
    }()

    @ViewBuilder
    private func segmentCard(_ seg: SegmentResult) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            // Header: timestamp + speaker badge + offline/refined badges
            HStack(spacing: 6) {
                Text(Self.segmentTimeFormatter.string(from: seg.createdAt))
                    .font(.caption2.monospacedDigit())
                    .foregroundStyle(.white.opacity(0.35))
                if showSpeakerColors {
                    SpeakerBadge(speakerId: seg.speakerId)
                }
                if seg.isOffline {
                    Image(systemName: "wifi.slash")
                        .font(.caption2)
                        .foregroundStyle(.orange.opacity(0.7))
                }
                if seg.isRefined {
                    Text("refined")
                        .font(.caption2)
                        .foregroundStyle(.cyan.opacity(0.6))
                }
                Spacer()
                if seg.status == .uploading || seg.status == .transcribed || seg.status == .translated {
                    ProgressView()
                        .tint(.white.opacity(0.3))
                        .scaleEffect(0.6)
                }
            }

            if seg.status == .uploading || seg.status == .transcribed || seg.status == .translated {
                if !seg.transcription.isEmpty {
                    Text(seg.transcription)
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.3))
                        .lineLimit(2)
                }
            } else {
                if displayMode != .translation && !seg.transcription.isEmpty {
                    Text(seg.transcription)
                        .font(.subheadline)
                        .foregroundStyle(.white.opacity(seg.isFinal ? 0.9 : 0.4))
                }
                if displayMode != .original && !seg.translation.isEmpty {
                    Text(seg.translation)
                        .font(.subheadline)
                        .foregroundStyle(.white.opacity(seg.isFinal ? 0.6 : 0.25))
                }
                if let err = seg.errorMessage {
                    Text(err)
                        .font(.caption2)
                        .foregroundStyle(.red.opacity(0.7))
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(.white.opacity(highlightedSegmentId == seg.id ? 0.08 : 0.04))
        )
        .overlay(
            // Speaker color left accent bar
            showSpeakerColors && seg.speakerId != nil
                ? RoundedRectangle(cornerRadius: 12)
                    .fill(.clear)
                    .overlay(alignment: .leading) {
                        if let color = SpeakerColors.color(for: seg.speakerId) {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(color.opacity(0.7))
                                .frame(width: 3)
                                .padding(.vertical, 4)
                        }
                    }
                    .clipped()
                : nil
        )
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                highlightedSegmentId = highlightedSegmentId == seg.id ? nil : seg.id
            }
        }
    }

    @ViewBuilder
    private func segmentFlowColumn(keyPath: KeyPath<SegmentResult, String>, isFinalOpacity: Double, pendingOpacity: Double) -> some View {
        let finalSegs = displaySegments.filter { $0.isFinal }
        let pendingSegs = displaySegments.filter { !$0.isFinal }
        let pendingText = pendingSegs.compactMap { seg -> String? in
            let t = seg[keyPath: keyPath]
            return t.isEmpty ? nil : t
        }.joined(separator: " ")

        VStack(alignment: .leading, spacing: 4) {
            // Show loading if nothing yet
            if finalSegs.isEmpty && pendingText.isEmpty && hasPending {
                ProgressView()
                    .tint(.white.opacity(0.3))
                    .scaleEffect(0.8)
            }

            // Final segments as continuous text (white)
            if !finalSegs.isEmpty {
                Text(buildFlowText(segments: finalSegs, keyPath: keyPath, opacity: isFinalOpacity))
                    .font(.subheadline)
            }

            // All pending segments combined as single gray pulsing text
            if !pendingText.isEmpty {
                PendingFlowText(text: pendingText, font: .subheadline, baseOpacity: pendingOpacity)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func buildFlowText(segments: [SegmentResult], keyPath: KeyPath<SegmentResult, String>, opacity: Double) -> AttributedString {
        var result = AttributedString()
        var lastSpeakerId: String? = nil

        for seg in segments {
            let text = seg[keyPath: keyPath]
            if text.isEmpty { continue }

            // Insert speaker label when speaker changes
            if showSpeakerColors,
               let currentSpeaker = seg.speakerId,
               currentSpeaker != lastSpeakerId {
                if !result.characters.isEmpty {
                    result += AttributedString("\n")
                }
                if let label = SpeakerColors.shortLabel(for: currentSpeaker),
                   let color = SpeakerColors.color(for: currentSpeaker) {
                    var badge = AttributedString("【\(label)】")
                    badge.foregroundColor = color.opacity(0.9)
                    badge.font = .caption2.bold()
                    result += badge
                }
                lastSpeakerId = currentSpeaker
            } else if !result.characters.isEmpty {
                result += AttributedString(" ")
            }

            var attr = AttributedString(text)
            // NOTE: Do NOT use attr.link here — iOS forces link text to
            // accent/tint color, overriding foregroundColor on many versions.
            attr.foregroundColor = .white.opacity(opacity)

            if highlightedSegmentId == seg.id {
                attr.backgroundColor = Color.yellow.opacity(0.15)
            }

            // Speaker color tint (subtle, only when speaker is identified and enabled)
            if showSpeakerColors, let speakerColor = SpeakerColors.color(for: seg.speakerId) {
                attr.foregroundColor = speakerColor.opacity(0.85)
            } else if seg.isOffline {
                attr.foregroundColor = .orange.opacity(0.7)
            }

            result += attr
        }
        return result
    }

    private func handleSegmentTap(url: URL) {
        guard url.scheme == "segment",
              let host = url.host,
              let id = UUID(uuidString: host) else { return }

        withAnimation(.easeInOut(duration: 0.2)) {
            highlightedSegmentId = highlightedSegmentId == id ? nil : id
        }
    }

    // MARK: - Broadcast

    private var broadcastExtensionBundleID: String {
        #if DEBUG
        "org.lzqqq.interpretation.debug.broadcast"
        #else
        "org.lzqqq.interpretation.broadcast"
        #endif
    }

    // MARK: - Footer

    private var footer: some View {
        Text("留学宝")
            .font(.caption2)
            .foregroundStyle(.white.opacity(0.18))
            .padding(.vertical, 10)
    }

    private var exportMenu: some View {
        Menu {
            Button {
                copyToPasteboard(combinedTranscription)
            } label: {
                Label("复制原文", systemImage: "doc.on.doc")
            }
            .disabled(combinedTranscription.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

            Button {
                copyToPasteboard(combinedTranslation)
            } label: {
                Label("复制译文", systemImage: "doc.on.doc")
            }
            .disabled(combinedTranslation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

            Button {
                let both: String
                if combinedTranscription.isEmpty { both = combinedTranslation }
                else if combinedTranslation.isEmpty { both = combinedTranscription }
                else { both = combinedTranscription + "\n\n" + combinedTranslation }
                copyToPasteboard(both)
            } label: {
                Label("复制原文+译文", systemImage: "doc.on.doc")
            }
            .disabled(
                combinedTranscription.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
                combinedTranslation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            )

            Divider()

            Button {
                exportAndShare(format: .pdf)
            } label: {
                Label("导出 PDF", systemImage: "doc.richtext")
            }
            .disabled(vm.segments.isEmpty)

            Button {
                exportAndShare(format: .txt)
            } label: {
                Label("导出 TXT", systemImage: "square.and.arrow.up")
            }
            .disabled(vm.segments.isEmpty)
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "square.and.arrow.up")
                    .font(.caption2)
                Text("导出")
                    .font(.caption)
            }
            .foregroundStyle(.white.opacity(0.35))
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(.white.opacity(0.05))
            .clipShape(Capsule())
        }
    }

    @ViewBuilder
    private var resultsContextMenu: some View {
        Button {
            copyToPasteboard(combinedTranscription)
        } label: {
            Label("复制原文", systemImage: "doc.on.doc")
        }
        .disabled(combinedTranscription.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

        Button {
            copyToPasteboard(combinedTranslation)
        } label: {
            Label("复制译文", systemImage: "doc.on.doc")
        }
        .disabled(combinedTranslation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

        Divider()

        Button {
            exportAndShare(format: .pdf)
        } label: {
            Label("导出 PDF", systemImage: "doc.richtext")
        }
        .disabled(vm.segments.isEmpty)

        Button {
            exportAndShare(format: .txt)
        } label: {
            Label("导出 TXT", systemImage: "square.and.arrow.up")
        }
        .disabled(vm.segments.isEmpty)
    }

    private var displayModeSwipeGesture: some Gesture {
        DragGesture(minimumDistance: 28, coordinateSpace: .local)
            .onEnded { value in
                guard isPadLayout else { return }

                let dx = value.translation.width
                let dy = value.translation.height
                guard abs(dx) > abs(dy), abs(dx) > 44 else { return }

                let nextMode = dx < 0
                    ? nextDisplayMode(from: displayMode)
                    : previousDisplayMode(from: displayMode)
                guard nextMode != displayMode else { return }

                UIImpactFeedbackGenerator(style: .light).impactOccurred()
                withAnimation(.easeInOut(duration: 0.2)) {
                    displayMode = nextMode
                }
            }
    }

    private func nextDisplayMode(from mode: DisplayMode) -> DisplayMode {
        let modes = DisplayMode.allCases
        guard let index = modes.firstIndex(of: mode) else { return mode }
        let nextIndex = modes.index(after: index)
        return nextIndex < modes.endIndex ? modes[nextIndex] : modes[modes.startIndex]
    }

    private func previousDisplayMode(from mode: DisplayMode) -> DisplayMode {
        let modes = DisplayMode.allCases
        guard let index = modes.firstIndex(of: mode) else { return mode }
        if index == modes.startIndex {
            return modes[modes.index(before: modes.endIndex)]
        }
        return modes[modes.index(before: index)]
    }

    private func exportAndShare(format: InterpretationExportFormat) {
        let segments = vm.segments
        let sourceLang = vm.sourceLang
        let targetLang = vm.targetLang
        let apiBaseURL = vm.apiBaseURL

        Task {
            do {
                let url = try await Task.detached(priority: .utility) {
                    try InterpretationExporter.exportToTemporaryFile(
                        segments: segments,
                        sourceLang: sourceLang,
                        targetLang: targetLang,
                        apiBaseURL: apiBaseURL,
                        format: format
                    )
                }.value
                self.sharePayload = ShareSheetPayload(items: [url])
            } catch {
                self.vm.lastError = error.localizedDescription
            }
        }
    }

    private func copyToPasteboard(_ text: String) {
        UIPasteboard.general.string = text
        showToast("已复制")
    }

    private func showToast(_ message: String) {
        withAnimation(.easeInOut(duration: 0.12)) {
            toastMessage = message
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
            withAnimation(.easeInOut(duration: 0.2)) {
                toastMessage = nil
            }
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Binding var apiBaseURL: String
    @ObservedObject var authVM: AuthViewModel
    @ObservedObject var vm: InterpretationViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var healthText: String?
    @State private var isTestingHealth = false
    @State private var groqKeyInput = ""
    @State private var groqKeyMessage: String?
    @State private var isSavingKey = false
    @State private var showDevOptions = false
    @State private var devTapCount = 0
    @State private var showingCreditStore = false
    @AppStorage("showSpeakerColors") private var showSpeakerColors: Bool = true
    @AppStorage("vadEnabled") private var vadEnabled: Bool = true
    @AppStorage("vadThresholdDb") private var vadThresholdDb: Double = -40.0
    @AppStorage("vadSilenceMs") private var vadSilenceMs: Int = 300
    @AppStorage("maxSegmentSeconds") private var maxSegmentSeconds: Double = 4.0
    @State private var isEditingKey = false

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text("转录模式")) {
                    if vm.creditBalance > 0 {
                        // Has credits: show full mode picker
                        Picker("模式", selection: $vm.asrTier) {
                            Text("Free").tag("free")
                            Text("Premium").tag("premium")
                        }
                        .onChange(of: vm.asrTier) { newTier in
                            if newTier == "premium" {
                                if authVM.user == nil {
                                    vm.asrTier = "free"
                                    groqKeyMessage = "请先登录后使用高级模式"
                                    return
                                }
                                Task { await vm.fetchCreditBalance() }
                            }
                        }

                        if vm.asrTier == "premium" {
                            HStack {
                                Text("余额")
                                Spacer()
                                Text("\(vm.creditBalance / 60) 分钟 \(vm.creditBalance % 60) 秒")
                                    .foregroundStyle(.secondary)
                            }

                            Button {
                                showingCreditStore = true
                            } label: {
                                HStack {
                                    Image(systemName: "cart")
                                    Text("购买额度")
                                }
                            }

                            Toggle("人声识别", isOn: $vm.speakerEnabled)

                            if vm.speakerEnabled {
                                Picker("识别方式", selection: $vm.speakerProvider) {
                                    Text("GPU识别").tag("gpu")
                                    Text("通义听悟（即将推出）").tag("tingwu")
                                }

                                if vm.speakerProvider == "gpu" {
                                    HStack {
                                        Image(systemName: "info.circle")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                        Text("使用 GPU 服务器进行说话人分离")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                    } else {
                        // No credits: show upgrade prompt
                        HStack {
                            Text("当前模式")
                            Spacer()
                            Text("免费")
                                .foregroundStyle(.secondary)
                        }

                        Button {
                            showingCreditStore = true
                        } label: {
                            HStack {
                                Image(systemName: "sparkles")
                                Text("升级到高级模式")
                            }
                        }

                        Text("高级模式提供更高精度的语音识别和说话人识别功能")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Section(header: Text("显示")) {
                    Toggle("说话人颜色", isOn: $showSpeakerColors)
                }

                Section(header: Text("账户")) {
                    if let user = authVM.user {
                        HStack {
                            Text("邮箱")
                            Spacer()
                            Text(user.email)
                                .foregroundStyle(.secondary)
                        }

                        if isEditingKey {
                            HStack {
                                Text("API Key")
                                TextField("gsk_...", text: $groqKeyInput)
                                    .autocorrectionDisabled()
                                    .textInputAutocapitalization(.never)
                                    .font(.system(.body, design: .monospaced))
                                    .multilineTextAlignment(.trailing)
                            }

                            Button {
                                if let url = URL(string: "https://console.groq.com/keys") {
                                    UIApplication.shared.open(url)
                                }
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "questionmark.circle")
                                        .font(.caption)
                                    Text("获取 API Key")
                                        .font(.caption)
                                }
                            }
                        } else {
                            HStack {
                                Text("API Key")
                                Spacer()
                                if groqKeyInput.isEmpty {
                                    Text("未设置")
                                        .foregroundStyle(.secondary)
                                } else {
                                    Text(maskedKey(groqKeyInput))
                                        .font(.system(.body, design: .monospaced))
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .contentShape(Rectangle())
                            .onTapGesture { isEditingKey = true }
                        }

                        if let msg = groqKeyMessage {
                            Text(msg)
                                .font(.footnote)
                                .foregroundStyle(msg.contains("success") || msg.contains("成功") || msg.contains("已保存") ? .green : .red)
                        }
                    } else {
                        Text("加载中...")
                            .foregroundStyle(.secondary)
                    }
                }

                // Developer options: hidden by default, tap version 5 times to reveal
                if showDevOptions {
                    Section(header: Text("Backend")) {
                        TextField("API Base URL", text: $apiBaseURL)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                    }

                    Section(header: Text("Connection")) {
                        Button(isTestingHealth ? "Testing..." : "Test /health") {
                            healthText = nil
                            isTestingHealth = true
                            Task {
                                do {
                                    let client = try APIClient(baseURLString: apiBaseURL)
                                    let health = try await client.health()
                                    healthText = "status=\(health.status), api_key_configured=\(health.api_key_configured)"
                                } catch {
                                    healthText = error.localizedDescription
                                }
                                isTestingHealth = false
                            }
                        }
                        .disabled(isTestingHealth)

                        if let healthText {
                            Text(healthText)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    }

                    Section(header: Text("Segmentation (VAD)")) {
                        Toggle("VAD enabled", isOn: $vadEnabled)

                        Stepper(value: $maxSegmentSeconds, in: 2...10, step: 0.5) {
                            Text("Max segment: \(String(format: "%.1f", maxSegmentSeconds))s")
                        }

                        Stepper(value: $vadSilenceMs, in: 150...1500, step: 50) {
                            Text("Silence: \(vadSilenceMs)ms")
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Threshold: \(String(format: "%.0f", vadThresholdDb)) dB")
                            Slider(value: $vadThresholdDb, in: (-60)...(-20), step: 1)
                        }
                    }
                }

                // Hidden dev options trigger: tap navigation title area 5 times
                Section {} footer: {
                    Color.clear
                        .frame(height: 1)
                        .onTapGesture {
                            devTapCount += 1
                            if devTapCount >= 5 {
                                showDevOptions.toggle()
                                devTapCount = 0
                            }
                        }
                }
            }
            .navigationTitle("设置")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    let trimmed = groqKeyInput.trimmingCharacters(in: .whitespacesAndNewlines)
                    let serverKey = authVM.user?.groq_api_key ?? ""
                    let keyChanged = trimmed != serverKey

                    if isSavingKey {
                        ProgressView().scaleEffect(0.8)
                    } else if keyChanged {
                        Button("Update") {
                            isSavingKey = true
                            groqKeyMessage = nil
                            Task {
                                if !trimmed.isEmpty {
                                    // Validate key from device first
                                    let validation = await Self.validateGroqKey(trimmed)
                                    if let error = validation {
                                        groqKeyMessage = error
                                        isSavingKey = false
                                        return
                                    }
                                }
                                // Save to server (empty = clear key)
                                let result = await authVM.updateGroqKey(trimmed)
                                if result.contains("success") || result.contains("成功") {
                                    // Sync back to user model
                                    authVM.user?.groq_api_key = trimmed
                                    authVM.user?.has_groq_key = !trimmed.isEmpty
                                    groqKeyMessage = "Key 已保存"
                                    isSavingKey = false
                                    try? await Task.sleep(nanoseconds: 800_000_000)
                                    dismiss()
                                    return
                                }
                                groqKeyMessage = result
                                isSavingKey = false
                            }
                        }
                    } else {
                        Button("Done") { dismiss() }
                    }
                }
            }
            .sheet(isPresented: $showingCreditStore) {
                CreditStoreView(vm: vm, baseURLString: apiBaseURL)
            }
            .onAppear {
                // Pre-populate Groq key from server profile
                if let key = authVM.user?.groq_api_key, !key.isEmpty {
                    groqKeyInput = key
                }
                Task { await vm.fetchCreditBalance() }
            }
        }
    }

    private func maskedKey(_ key: String) -> String {
        let trimmed = key.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count > 8 else { return String(repeating: "•", count: trimmed.count) }
        let prefix = String(trimmed.prefix(4))
        let suffix = String(trimmed.suffix(4))
        return "\(prefix)••••\(suffix)"
    }

    /// Validate Groq API key by calling Groq API directly from the device.
    /// Returns nil on success, or an error message string on failure.
    /// Validate Groq key from device. Only reject on 401 (definitely invalid).
    /// 403 means the key exists but /models is restricted — key may still work for ASR.
    private static func validateGroqKey(_ key: String) async -> String? {
        let trimmed = key.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.hasPrefix("gsk_") else {
            return "Key 应以 gsk_ 开头"
        }
        guard let url = URL(string: "https://api.groq.com/openai/v1/models") else {
            return nil
        }
        var request = URLRequest(url: url)
        request.setValue("Bearer \(trimmed)", forHTTPHeaderField: "Authorization")
        request.timeoutInterval = 10
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else { return nil }
            if http.statusCode == 401 { return "Key 无效（认证失败）" }
            // 200 = valid, 403 = key exists but restricted endpoint, others = accept anyway
            return nil
        } catch {
            // Network error — don't block, key will be validated during actual use
            return nil
        }
    }
}

// MARK: - Broadcast Picker Button

/// Programmatically trigger the system broadcast picker without embedding it in the view hierarchy.
enum BroadcastPickerTrigger {
    static func show(preferredExtension: String) {
        let picker = RPSystemBroadcastPickerView(frame: .zero)
        picker.preferredExtension = preferredExtension
        picker.showsMicrophoneButton = false

        // Find the internal UIButton and tap it programmatically
        if let button = picker.subviews.compactMap({ $0 as? UIButton }).first {
            button.sendActions(for: .touchUpInside)
        }
    }
}

// MARK: - Apple Translation Setup (iOS 18+)

extension View {
    @ViewBuilder
    func translationSetup(vm: InterpretationViewModel, sourceLang: String, targetLang: String) -> some View {
        if #available(iOS 18.0, *) {
            self.modifier(TranslationSetupModifier(vm: vm, sourceLang: sourceLang, targetLang: targetLang))
        } else {
            self
        }
    }
}

@available(iOS 18.0, *)
private struct TranslationSetupModifier: ViewModifier {
    let vm: InterpretationViewModel
    let sourceLang: String
    let targetLang: String
    @State private var config: TranslationSession.Configuration?

    func body(content: Content) -> some View {
        content
            .translationTask(config) { session in
                await MainActor.run {
                    vm.translationSession = session
                }
            }
            .onAppear {
                config = makeConfig()
            }
            .onChange(of: sourceLang) {
                config = makeConfig()
            }
            .onChange(of: targetLang) {
                config = makeConfig()
            }
    }

    private func makeConfig() -> TranslationSession.Configuration {
        let source = Self.localeLanguage(forSourceCode: sourceLang)
        let target = Self.localeLanguage(forTargetName: targetLang)
        return .init(source: source, target: target)
    }

    static func localeLanguage(forSourceCode code: String) -> Locale.Language {
        switch code.lowercased() {
        case "zh": return Locale.Language(identifier: "zh-Hans")
        case "yue": return Locale.Language(identifier: "yue")
        default: return Locale.Language(identifier: code)
        }
    }

    static func localeLanguage(forTargetName name: String) -> Locale.Language {
        switch name {
        case "Chinese": return Locale.Language(identifier: "zh-Hans")
        case "Cantonese": return Locale.Language(identifier: "yue")
        case "English": return Locale.Language(identifier: "en")
        case "Japanese": return Locale.Language(identifier: "ja")
        case "Korean": return Locale.Language(identifier: "ko")
        case "French": return Locale.Language(identifier: "fr")
        case "German": return Locale.Language(identifier: "de")
        case "Spanish": return Locale.Language(identifier: "es")
        case "Portuguese": return Locale.Language(identifier: "pt")
        case "Russian": return Locale.Language(identifier: "ru")
        case "Arabic": return Locale.Language(identifier: "ar")
        case "Italian": return Locale.Language(identifier: "it")
        case "Thai": return Locale.Language(identifier: "th")
        case "Vietnamese": return Locale.Language(identifier: "vi")
        case "Indonesian": return Locale.Language(identifier: "id")
        case "Malay": return Locale.Language(identifier: "ms")
        case "Turkish": return Locale.Language(identifier: "tr")
        case "Hindi": return Locale.Language(identifier: "hi")
        case "Dutch": return Locale.Language(identifier: "nl")
        case "Polish": return Locale.Language(identifier: "pl")
        case "Swedish": return Locale.Language(identifier: "sv")
        case "Danish": return Locale.Language(identifier: "da")
        case "Finnish": return Locale.Language(identifier: "fi")
        case "Czech": return Locale.Language(identifier: "cs")
        case "Greek": return Locale.Language(identifier: "el")
        case "Hungarian": return Locale.Language(identifier: "hu")
        case "Romanian": return Locale.Language(identifier: "ro")
        case "Persian": return Locale.Language(identifier: "fa")
        case "Filipino": return Locale.Language(identifier: "fil")
        case "Macedonian": return Locale.Language(identifier: "mk")
        default: return Locale.Language(identifier: name.lowercased())
        }
    }
}
