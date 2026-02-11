import AVFoundation
import SwiftUI

struct LocalRecordingsView: View {
    @ObservedObject var vm: InterpretationViewModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @State private var query: String = ""
    @State private var sharePayload: ShareSheetPayload?
    @State private var selectedRecordingID: UUID?

    private var filteredRecordings: [LocalInterpretationRecording] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return vm.localRecordings }

        let lower = trimmed.lowercased()
        return vm.localRecordings.filter { item in
            item.title.lowercased().contains(lower) ||
            item.transcription.lowercased().contains(lower) ||
            item.translation.lowercased().contains(lower)
        }
    }

    private var isPadLayout: Bool {
        UIDevice.current.userInterfaceIdiom == .pad || horizontalSizeClass == .regular
    }

    private var selectedRecording: LocalInterpretationRecording? {
        guard let selectedRecordingID else { return nil }
        return vm.localRecordings.first(where: { $0.id == selectedRecordingID })
    }

    var body: some View {
        Group {
            if isPadLayout {
                NavigationSplitView {
                    List(selection: $selectedRecordingID) {
                        if filteredRecordings.isEmpty {
                            Text("暂无本地录音")
                                .foregroundStyle(.secondary)
                        } else {
                            ForEach(filteredRecordings) { item in
                                LocalRecordingRow(recording: item)
                                    .contentShape(Rectangle())
                                    .onTapGesture { selectedRecordingID = item.id }
                                    .tag(item.id)
                                    .listRowBackground(
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(Color(.secondarySystemGroupedBackground))
                                    )
                                    .listRowSeparator(.hidden)
                                    .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                        Button(role: .destructive) {
                                            if selectedRecordingID == item.id {
                                                selectedRecordingID = nil
                                            }
                                            vm.deleteLocalRecording(item)
                                            syncSelectedRecording()
                                        } label: {
                                            Label("删除", systemImage: "trash")
                                        }
                                        if let audioURL = vm.audioURL(for: item) {
                                            Button {
                                                sharePayload = ShareSheetPayload(items: [audioURL])
                                            } label: {
                                                Label("分享", systemImage: "square.and.arrow.up")
                                            }
                                            .tint(.blue)
                                        }
                                    }
                            }
                        }
                    }
                    .listStyle(.plain)
                    .navigationTitle("All Recordings")
                    .searchable(text: $query, prompt: "搜索录音或翻译内容")
                    .toolbar {
                        ToolbarItem(placement: .topBarLeading) {
                            Button("关闭") { dismiss() }
                                .keyboardShortcut(.escape, modifiers: [])
                        }
                        ToolbarItemGroup(placement: .topBarTrailing) {
                            if let selectedRecording,
                               let audioURL = vm.audioURL(for: selectedRecording) {
                                Button {
                                    sharePayload = ShareSheetPayload(items: [audioURL])
                                } label: {
                                    Image(systemName: "square.and.arrow.up")
                                }
                                .keyboardShortcut("s", modifiers: [.command, .shift])
                                .help("⇧⌘S 分享所选录音")
                            }

                            Button(role: .destructive) {
                                deleteSelectedRecording()
                            } label: {
                                Image(systemName: "trash")
                            }
                            .disabled(selectedRecording == nil)
                            .keyboardShortcut(.delete, modifiers: [.command])
                            .help("⌘⌫ 删除所选录音")
                        }
                    }
                } detail: {
                    if let selectedRecording {
                        NavigationStack {
                            LocalRecordingDetailView(recording: selectedRecording, vm: vm)
                        }
                    } else {
                        VStack(spacing: 10) {
                            Image(systemName: "waveform")
                                .font(.system(size: 32))
                            Text("选择一条录音")
                                .font(.headline)
                            Text("在左侧列表选择后可播放和分享")
                                .font(.subheadline)
                        }
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    }
                }
                .navigationSplitViewStyle(.balanced)
            } else {
                NavigationStack {
                    List {
                        if filteredRecordings.isEmpty {
                            Text("暂无本地录音")
                                .foregroundStyle(.secondary)
                        } else {
                            ForEach(filteredRecordings) { item in
                                NavigationLink {
                                    LocalRecordingDetailView(recording: item, vm: vm)
                                } label: {
                                    LocalRecordingRow(recording: item)
                                }
                                .listRowBackground(
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(Color(.secondarySystemGroupedBackground))
                                )
                                .listRowSeparator(.hidden)
                                .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                    Button(role: .destructive) {
                                        vm.deleteLocalRecording(item)
                                    } label: {
                                        Label("删除", systemImage: "trash")
                                    }
                                    if let audioURL = vm.audioURL(for: item) {
                                        Button {
                                            sharePayload = ShareSheetPayload(items: [audioURL])
                                        } label: {
                                            Label("分享", systemImage: "square.and.arrow.up")
                                        }
                                        .tint(.blue)
                                    }
                                }
                            }
                        }
                    }
                    .listStyle(.plain)
                    .navigationTitle("All Recordings")
                    .searchable(text: $query, prompt: "搜索录音或翻译内容")
                    .toolbar {
                        ToolbarItem(placement: .topBarLeading) {
                            Button("关闭") { dismiss() }
                                .keyboardShortcut(.escape, modifiers: [])
                        }
                    }
                }
            }
        }
        .onAppear {
            syncSelectedRecording()
        }
        .onChange(of: vm.localRecordings.map(\.id)) { _ in
            syncSelectedRecording()
        }
        .onChange(of: filteredRecordings.map(\.id)) { _ in
            syncSelectedRecording()
        }
        .sheet(item: $sharePayload) { payload in
            ShareSheet(items: payload.items)
        }
    }

    private func syncSelectedRecording() {
        guard isPadLayout else { return }
        let ids = Set(filteredRecordings.map(\.id))
        if let selectedRecordingID, ids.contains(selectedRecordingID) {
            return
        }
        selectedRecordingID = filteredRecordings.first?.id
    }

    private func deleteSelectedRecording() {
        guard let selectedRecording else { return }
        vm.deleteLocalRecording(selectedRecording)
        syncSelectedRecording()
    }
}

private struct LocalRecordingRow: View {
    let recording: LocalInterpretationRecording

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(recording.title)
                .font(.headline)
                .lineLimit(1)

            HStack {
                Text(dateString(recording.createdAt))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Spacer()

                Text(durationString(recording.durationSeconds))
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct LocalRecordingDetailView: View {
    let recording: LocalInterpretationRecording
    @ObservedObject var vm: InterpretationViewModel
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @StateObject private var player = AudioPlaybackController()
    @State private var sharePayload: ShareSheetPayload?

    private var recordingAudioURL: URL? {
        vm.audioURL(for: recording)
    }

    private var isPadLayout: Bool {
        UIDevice.current.userInterfaceIdiom == .pad || horizontalSizeClass == .regular
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                playbackCard
                transcriptCard(title: "Original", text: recording.transcription)
                transcriptCard(title: "Translation", text: recording.translation)
            }
            .padding(16)
        }
        .navigationTitle(recording.title)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            player.load(url: recordingAudioURL)
        }
        .onDisappear {
            player.stop()
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                if let audioURL = recordingAudioURL {
                    Button {
                        sharePayload = ShareSheetPayload(items: [audioURL])
                    } label: {
                        Image(systemName: "square.and.arrow.up")
                    }
                    .keyboardShortcut("s", modifiers: [.command, .shift])
                    .help("⇧⌘S 分享音频")
                }
            }
        }
        .sheet(item: $sharePayload) { payload in
            ShareSheet(items: payload.items)
        }
    }

    private var playbackCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("本地录音")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Spacer()
                Text(durationString(recording.durationSeconds))
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
            }

            if player.hasAudio {
                HStack(spacing: 24) {
                    Button {
                        player.seek(by: -15)
                    } label: {
                        Image(systemName: "gobackward.15")
                            .font(.title3)
                    }
                    .buttonStyle(.plain)
                    .keyboardShortcut("[", modifiers: [.command])
                    .help("⌘[ 后退 15 秒")

                    Button {
                        player.togglePlayPause()
                    } label: {
                        Image(systemName: player.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                            .font(.system(size: 40))
                    }
                    .buttonStyle(.plain)
                    .keyboardShortcut(.space, modifiers: [])
                    .help("Space 播放/暂停")

                    Button {
                        player.seek(by: 15)
                    } label: {
                        Image(systemName: "goforward.15")
                            .font(.title3)
                    }
                    .buttonStyle(.plain)
                    .keyboardShortcut("]", modifiers: [.command])
                    .help("⌘] 前进 15 秒")
                }
                .frame(maxWidth: .infinity)

                Slider(
                    value: Binding(
                        get: { player.progress },
                        set: { player.seekToProgress($0) }
                    ),
                    in: 0...1
                )

                HStack {
                    Text(durationString(player.currentTime))
                    Spacer()
                    Text(durationString(player.totalDuration))
                }
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)

                if isPadLayout {
                    Text("Space 播放/暂停  ·  ⌘[ 后退 15 秒  ·  ⌘] 前进 15 秒  ·  ⇧⌘S 分享")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .opacity(0.8)
                }
            } else {
                Text("该条记录无可播放音频")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(14)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private func transcriptCard(title: String, text: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.semibold)

            if text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                Text("(empty)")
                    .foregroundStyle(.secondary)
            } else {
                Text(text)
                    .font(.body)
                    .textSelection(.enabled)
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

@MainActor
final class AudioPlaybackController: NSObject, ObservableObject {
    @Published var isPlaying: Bool = false
    @Published var currentTime: TimeInterval = 0
    @Published var totalDuration: TimeInterval = 0
    @Published var hasAudio: Bool = false

    private var player: AVAudioPlayer?
    private var timer: Timer?

    var progress: Double {
        guard totalDuration > 0 else { return 0 }
        return min(1, max(0, currentTime / totalDuration))
    }

    func load(url: URL?) {
        stop()
        guard let url else {
            hasAudio = false
            return
        }
        do {
            let p = try AVAudioPlayer(contentsOf: url)
            p.prepareToPlay()
            player = p
            hasAudio = true
            totalDuration = p.duration
            currentTime = 0
        } catch {
            hasAudio = false
            player = nil
            totalDuration = 0
            currentTime = 0
        }
    }

    func togglePlayPause() {
        guard let player else { return }
        if player.isPlaying {
            player.pause()
            stopTimer()
            isPlaying = false
        } else {
            player.play()
            startTimer()
            isPlaying = true
        }
    }

    func seek(by seconds: TimeInterval) {
        guard let player else { return }
        let newTime = min(max(0, player.currentTime + seconds), player.duration)
        player.currentTime = newTime
        currentTime = newTime
    }

    func seekToProgress(_ progress: Double) {
        guard let player else { return }
        let p = min(max(progress, 0), 1)
        let time = player.duration * p
        player.currentTime = time
        currentTime = time
    }

    func stop() {
        player?.stop()
        player = nil
        stopTimer()
        isPlaying = false
        currentTime = 0
        totalDuration = 0
    }

    private func startTimer() {
        stopTimer()
        timer = Timer.scheduledTimer(
            timeInterval: 0.2,
            target: self,
            selector: #selector(handleTimerTick),
            userInfo: nil,
            repeats: true
        )
    }

    @objc private func handleTimerTick() {
        guard let player else {
            stopTimer()
            isPlaying = false
            currentTime = 0
            return
        }
        currentTime = player.currentTime
        if isPlaying, !player.isPlaying {
            stopTimer()
            isPlaying = false
        }
    }

    private func stopTimer() {
        timer?.invalidate()
        timer = nil
    }
}

private func dateString(_ date: Date) -> String {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.dateFormat = "d MMM yyyy HH:mm"
    return f.string(from: date)
}

private func durationString(_ seconds: TimeInterval) -> String {
    let total = max(0, Int(seconds.rounded()))
    let h = total / 3600
    let m = (total % 3600) / 60
    let s = total % 60
    if h > 0 {
        return String(format: "%d:%02d:%02d", h, m, s)
    }
    return String(format: "%d:%02d", m, s)
}
