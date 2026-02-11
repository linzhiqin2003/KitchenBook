import SwiftUI
import UniformTypeIdentifiers

// MARK: - Theme

extension Color {
    static let iosCard = Color(red: 28/255, green: 28/255, blue: 30/255)
    static let iosCard2 = Color(red: 44/255, green: 44/255, blue: 46/255)
    static let iosBlue = Color(red: 10/255, green: 132/255, blue: 255/255)
    static let iosRed = Color(red: 255/255, green: 69/255, blue: 58/255)
}

// MARK: - Shimmer Effect

struct ShimmerText: View {
    let text: String
    let font: Font
    let baseOpacity: Double
    @State private var pulse = false

    var body: some View {
        Text(text)
            .font(font)
            .foregroundStyle(.white.opacity(pulse ? baseOpacity + 0.15 : baseOpacity - 0.05))
            .animation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true), value: pulse)
            .onAppear { pulse = true }
    }
}

struct PendingFlowText: View {
    let text: String
    let font: Font
    let baseOpacity: Double
    @State private var pulse = false

    var body: some View {
        Text(text)
            .font(font)
            .foregroundStyle(.white.opacity(pulse ? baseOpacity + 0.12 : baseOpacity - 0.05))
            .animation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true), value: pulse)
            .onAppear { pulse = true }
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
        .onAppear { vm.authViewModel = authVM }
        .sheet(isPresented: $showingSettings) {
            SettingsView(apiBaseURL: vm.apiBaseURLBinding, authVM: authVM)
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

    private var header: some View {
        HStack {
            Text("留学宝")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(.white)
                .onLongPressGesture { showingSettings = true }

            Spacer()

            Text("实时转译")
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(.white.opacity(0.45))

            Button {
                showingLocalRecordings = true
            } label: {
                Image(systemName: "list.bullet.rectangle")
                    .font(.system(size: 14))
                    .foregroundStyle(.white.opacity(0.5))
            }
            .padding(.leading, 10)

            Button {
                authVM.logout()
            } label: {
                Image(systemName: "rectangle.portrait.and.arrow.right")
                    .font(.system(size: 14))
                    .foregroundStyle(.white.opacity(0.4))
            }
            .padding(.leading, 8)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
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
                    .frame(maxWidth: mainContentMaxWidth, alignment: .top)
                    .padding(.horizontal, 20)
                    .padding(.top, 16)
                    .padding(.bottom, 40)
            }
        }
    }

    private var phoneLayoutContent: some View {
        VStack(spacing: 24) {
            if !vm.isRecording {
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
            if !vm.isRecording {
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
    }

    // MARK: - Language Selectors

    private var languageSelectors: some View {
        HStack(spacing: 12) {
            LangPickerButton(label: "From", options: allSourceLanguages, selection: $vm.sourceLang)

            Image(systemName: "arrow.right")
                .font(.caption)
                .foregroundStyle(.white.opacity(0.25))
                .padding(.top, 22)

            LangPickerButton(label: "To", options: allTargetLanguages, selection: $vm.targetLang)
        }
    }

    // MARK: - Input Area

    private var inputArea: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 24)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 24)
                        .strokeBorder(.white.opacity(0.08))
                )

            VStack(spacing: 14) {
                ZStack {
                    // Waveform behind the button (only visible when recording)
                    if vm.isRecording {
                        WaveformView(levels: vm.waveformLevels, isActive: true)
                    }

                    if vm.isRecording {
                        PulseRing()
                    }

                    Button {
                        if vm.isRecording { vm.stop() } else { vm.start() }
                    } label: {
                        ZStack {
                            Circle()
                                .fill(vm.isRecording ? Color.iosRed : .white.opacity(0.1))
                                .frame(width: 64, height: 64)
                                .overlay(
                                    Circle().strokeBorder(
                                        vm.isRecording ? Color.iosRed.opacity(0.5) : .white.opacity(0.2),
                                        lineWidth: 2
                                    )
                                )
                                .shadow(color: vm.isRecording ? Color.iosRed.opacity(0.35) : .clear, radius: 16)

                            if vm.isRecording {
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(.white)
                                    .frame(width: 20, height: 20)
                            } else {
                                Image(systemName: "mic.fill")
                                    .font(.title2)
                                    .foregroundStyle(.white)
                            }
                        }
                    }

                    // Upload button (hidden when recording)
                    if !vm.isRecording {
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
                    .offset(x: 32, y: 24)
                    }
                }

                if vm.isRecording {
                    Text(String(format: "%02d:%02d", vm.recordingSeconds / 60, vm.recordingSeconds % 60))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(Color.iosRed.opacity(0.9))
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
                if isPadLayout {
                    Picker("Display Mode", selection: $displayMode) {
                        ForEach(DisplayMode.allCases, id: \.self) { mode in
                            Text(mode.title).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                    .labelsHidden()
                    .frame(maxWidth: 340)
                } else {
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
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            .padding(.bottom, 8)

            // Content columns
            resultsContent
                .padding(.horizontal, 16)
                .padding(.bottom, 12)

            Rectangle()
                .fill(.white.opacity(0.06))
                .frame(height: 1)

            // Stats + Clear
            HStack {
                Text("\(combinedTranscription.split(separator: " ").count) words")
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.2))

                Spacer()

                if isPadLayout {
                    Button {
                        exportAndShare(format: .pdf)
                    } label: {
                        Label("PDF", systemImage: "doc.richtext")
                            .font(.caption)
                    }
                    .foregroundStyle(.white.opacity(0.75))
                    .disabled(vm.segments.isEmpty)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(.white.opacity(0.05))
                    .clipShape(Capsule())

                    Button {
                        exportAndShare(format: .txt)
                    } label: {
                        Label("TXT", systemImage: "square.and.arrow.up")
                            .font(.caption)
                    }
                    .foregroundStyle(.white.opacity(0.75))
                    .disabled(vm.segments.isEmpty)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(.white.opacity(0.05))
                    .clipShape(Capsule())
                } else {
                    exportMenu
                }

                Button {
                    vm.clear()
                    highlightedSegmentId = nil
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "trash")
                            .font(.caption2)
                        Text("清空")
                            .font(.caption)
                    }
                    .foregroundStyle(.white.opacity(0.35))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(.white.opacity(0.05))
                    .clipShape(Capsule())
                }
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
            // Header: timestamp + refined badge
            HStack(spacing: 6) {
                Text(Self.segmentTimeFormatter.string(from: seg.createdAt))
                    .font(.caption2.monospacedDigit())
                    .foregroundStyle(.white.opacity(0.35))
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

            // Final segments as continuous tappable text (white)
            if !finalSegs.isEmpty {
                Text(buildFlowText(segments: finalSegs, keyPath: keyPath, opacity: isFinalOpacity))
                    .font(.subheadline)
                    .tint(.white.opacity(isFinalOpacity))
                    .environment(\.openURL, OpenURLAction { url in
                        handleSegmentTap(url: url)
                        return .handled
                    })
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
        for seg in segments {
            let text = seg[keyPath: keyPath]
            if text.isEmpty { continue }

            var attr = AttributedString(text)
            attr.link = URL(string: "segment://\(seg.id.uuidString)")

            if highlightedSegmentId == seg.id {
                attr.backgroundColor = Color.yellow.opacity(0.15)
            }

            if !result.characters.isEmpty {
                result += AttributedString(" ")
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

    // MARK: - Footer

    private var footer: some View {
        Text("Powered by Qwen")
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
    @Environment(\.dismiss) private var dismiss
    @State private var healthText: String?
    @State private var isTestingHealth = false
    @State private var groqKeyInput = ""
    @State private var groqKeyMessage: String?
    @State private var isSavingKey = false
    @State private var showDevOptions = false
    @State private var devTapCount = 0
    @AppStorage("vadEnabled") private var vadEnabled: Bool = true
    @AppStorage("vadThresholdDb") private var vadThresholdDb: Double = -40.0
    @AppStorage("vadSilenceMs") private var vadSilenceMs: Int = 300
    @AppStorage("maxSegmentSeconds") private var maxSegmentSeconds: Double = 4.0

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text("Account")) {
                    if let user = authVM.user {
                        HStack {
                            Text("Email")
                            Spacer()
                            Text(user.email)
                                .foregroundStyle(.secondary)
                        }
                        HStack {
                            Text("Groq API Key")
                            Spacer()
                            Text(user.has_groq_key == true ? "Configured" : "Not set")
                                .foregroundStyle(user.has_groq_key == true ? .green : .red)
                        }

                        TextField("gsk_...", text: $groqKeyInput)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                            .font(.footnote)

                        Button {
                            isSavingKey = true
                            groqKeyMessage = nil
                            Task {
                                let result = await authVM.updateGroqKey(groqKeyInput)
                                groqKeyMessage = result
                                if result.contains("success") || result.contains("成功") {
                                    groqKeyInput = ""
                                }
                                isSavingKey = false
                            }
                        } label: {
                            HStack {
                                if isSavingKey {
                                    ProgressView().scaleEffect(0.8)
                                }
                                Text(isSavingKey ? "Saving..." : "Update Groq Key")
                            }
                        }
                        .disabled(groqKeyInput.isEmpty || isSavingKey)

                        if let msg = groqKeyMessage {
                            Text(msg)
                                .font(.footnote)
                                .foregroundStyle(msg.contains("success") || msg.contains("成功") ? .green : .red)
                        }

                        Button {
                            if let url = URL(string: "https://console.groq.com/keys") {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "questionmark.circle")
                                    .font(.caption)
                                Text("Get Groq API Key")
                                    .font(.caption)
                            }
                        }
                    } else {
                        Text("Loading...")
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

                Section {
                    HStack {
                        Spacer()
                        Text("v1.0")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .onTapGesture {
                                devTapCount += 1
                                if devTapCount >= 5 {
                                    showDevOptions.toggle()
                                    devTapCount = 0
                                }
                            }
                        Spacer()
                    }
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
