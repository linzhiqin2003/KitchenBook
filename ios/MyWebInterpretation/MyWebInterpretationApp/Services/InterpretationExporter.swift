import Foundation
import CoreText
import UIKit
import UniformTypeIdentifiers

enum InterpretationExportFormat: String, CaseIterable, Sendable {
    case txt
    case csv
    case json
    case pdf

    var fileExtension: String { rawValue }

    var utType: UTType {
        switch self {
        case .txt:
            return .plainText
        case .csv:
            return .commaSeparatedText
        case .json:
            return .json
        case .pdf:
            return .pdf
        }
    }
}

enum InterpretationExportError: LocalizedError {
    case empty
    case encodingFailed

    var errorDescription: String? {
        switch self {
        case .empty:
            return "没有可导出的数据"
        case .encodingFailed:
            return "导出编码失败"
        }
    }
}

struct InterpretationExporter {
    private static func isoString(_ date: Date) -> String {
        // Date formatters are not guaranteed thread-safe; keep it local.
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f.string(from: date)
    }

    static func exportToTemporaryFile(
        segments: [SegmentResult],
        sourceLang: String,
        targetLang: String,
        apiBaseURL: String,
        format: InterpretationExportFormat
    ) throws -> URL {
        guard !segments.isEmpty else { throw InterpretationExportError.empty }

        let now = Date()
        let payload = buildPayload(
            segments: segments,
            sourceLang: sourceLang,
            targetLang: targetLang,
            apiBaseURL: apiBaseURL,
            exportedAt: now
        )

        let fileBaseName = suggestedBaseName(
            sourceLang: sourceLang,
            targetLang: targetLang,
            exportedAt: now
        )
        let fileName = "\(fileBaseName).\(format.fileExtension)"
        let fileURL = FileManager.default.temporaryDirectory.appendingPathComponent(fileName)

        switch format {
        case .txt:
            let text = renderPlainText(payload: payload)
            guard let data = text.data(using: .utf8) else {
                throw InterpretationExportError.encodingFailed
            }
            try data.write(to: fileURL, options: [.atomic])
        case .csv:
            let text = renderCSV(payload: payload)
            guard let data = text.data(using: .utf8) else {
                throw InterpretationExportError.encodingFailed
            }
            try data.write(to: fileURL, options: [.atomic])
        case .json:
            let data = try renderJSON(payload: payload)
            try data.write(to: fileURL, options: [.atomic])
        case .pdf:
            let data = try renderPDF(payload: payload)
            try data.write(to: fileURL, options: [.atomic])
        }

        return fileURL
    }

    static func buildPayload(
        segments: [SegmentResult],
        sourceLang: String,
        targetLang: String,
        apiBaseURL: String,
        exportedAt: Date
    ) -> InterpretationExportPayload {
        InterpretationExportPayload(
            exported_at: isoString(exportedAt),
            source_lang: sourceLang,
            target_lang: targetLang,
            api_base_url: apiBaseURL,
            segments: segments.map { seg in
                InterpretationExportPayload.Segment(
                    id: seg.id.uuidString,
                    seq: seg.seq,
                    created_at: isoString(seg.createdAt),
                    transcription: seg.transcription,
                    translation: seg.translation,
                    status: seg.status.rawValue,
                    error_message: seg.errorMessage
                )
            }
        )
    }

    static func renderJSON(payload: InterpretationExportPayload) throws -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return try encoder.encode(payload)
    }

    static func renderPlainText(payload: InterpretationExportPayload) -> String {
        let originals = payload.segments
            .map { $0.transcription.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: "\n")

        let translations = payload.segments
            .map { $0.translation.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: "\n")

        var lines: [String] = []
        lines.append("MyWebInterpretation Export")
        lines.append("exported_at: \(payload.exported_at)")
        lines.append("source_lang: \(payload.source_lang)")
        lines.append("target_lang: \(payload.target_lang)")
        lines.append("api_base_url: \(payload.api_base_url)")
        lines.append("segments: \(payload.segments.count)")
        lines.append("")
        lines.append("=== Original ===")
        lines.append(originals)
        lines.append("")
        lines.append("=== Translation ===")
        lines.append(translations)
        lines.append("")
        lines.append("=== Segments (details) ===")

        for seg in payload.segments.sorted(by: { $0.seq < $1.seq }) {
            lines.append("#\(seg.seq) [\(seg.created_at)] status=\(seg.status)")
            if let err = seg.error_message, !err.isEmpty {
                lines.append("error: \(err)")
            }
            if !seg.transcription.isEmpty {
                lines.append("original: \(seg.transcription)")
            }
            if !seg.translation.isEmpty {
                lines.append("translation: \(seg.translation)")
            }
            lines.append("")
        }

        return lines.joined(separator: "\n")
    }

    static func renderCSV(payload: InterpretationExportPayload) -> String {
        func csvField(_ s: String?) -> String {
            let value = s ?? ""
            let escaped = value.replacingOccurrences(of: "\"", with: "\"\"")
            return "\"\(escaped)\""
        }

        var rows: [String] = []
        rows.append([
            "seq",
            "created_at",
            "status",
            "transcription",
            "translation",
            "error_message",
        ].joined(separator: ","))

        for seg in payload.segments.sorted(by: { $0.seq < $1.seq }) {
            rows.append([
                "\(seg.seq)",
                csvField(seg.created_at),
                csvField(seg.status),
                csvField(seg.transcription),
                csvField(seg.translation),
                csvField(seg.error_message),
            ].joined(separator: ","))
        }

        return rows.joined(separator: "\n")
    }

    static func renderPDF(payload: InterpretationExportPayload) throws -> Data {
        let content = buildPDFAttributedString(payload: payload)

        // US Letter size at 72 DPI: 8.5x11 inches.
        let pageRect = CGRect(x: 0, y: 0, width: 612, height: 792)
        let margin: CGFloat = 36
        let footerHeight: CGFloat = 24
        let bodyRect = CGRect(
            x: margin,
            y: margin,
            width: pageRect.width - (margin * 2),
            height: pageRect.height - (margin * 2) - footerHeight
        )
        let textRect = CGRect(
            x: bodyRect.minX,
            y: pageRect.height - bodyRect.maxY,
            width: bodyRect.width,
            height: bodyRect.height
        )

        let format = UIGraphicsPDFRendererFormat()
        format.documentInfo = [
            kCGPDFContextCreator as String: "MyWebInterpretation",
            kCGPDFContextTitle as String: "Interpretation Export",
            kCGPDFContextAuthor as String: "MyWebInterpretation",
        ]

        let renderer = UIGraphicsPDFRenderer(bounds: pageRect, format: format)
        let framesetter = CTFramesetterCreateWithAttributedString(content as CFAttributedString)

        return renderer.pdfData { context in
            var currentRange = CFRange(location: 0, length: 0)
            var pageNumber = 1

            while currentRange.location < content.length {
                context.beginPage()

                let cgContext = context.cgContext
                cgContext.saveGState()
                cgContext.textMatrix = .identity
                cgContext.translateBy(x: 0, y: pageRect.height)
                cgContext.scaleBy(x: 1, y: -1)

                let path = CGPath(rect: textRect, transform: nil)
                let frame = CTFramesetterCreateFrame(framesetter, currentRange, path, nil)
                CTFrameDraw(frame, cgContext)
                cgContext.restoreGState()

                // Footer: page number (UIKit coordinates).
                let footer = "Page \(pageNumber)"
                let footerAttrs: [NSAttributedString.Key: Any] = [
                    .font: UIFont.systemFont(ofSize: 10),
                    .foregroundColor: UIColor.darkGray,
                ]
                let footerSize = (footer as NSString).size(withAttributes: footerAttrs)
                let footerRect = CGRect(
                    x: margin,
                    y: pageRect.height - margin - footerHeight + ((footerHeight - footerSize.height) / 2),
                    width: pageRect.width - (margin * 2),
                    height: footerHeight
                )
                (footer as NSString).draw(
                    in: footerRect,
                    withAttributes: footerAttrs.merging([.paragraphStyle: centeredParagraphStyle()], uniquingKeysWith: { $1 })
                )

                let visibleRange = CTFrameGetVisibleStringRange(frame)
                guard visibleRange.length > 0 else { break }
                currentRange.location += visibleRange.length
                pageNumber += 1
            }
        }
    }

    private static func centeredParagraphStyle() -> NSParagraphStyle {
        let p = NSMutableParagraphStyle()
        p.alignment = .center
        return p
    }

    private static func buildPDFAttributedString(payload: InterpretationExportPayload) -> NSAttributedString {
        let titleFont = UIFont.boldSystemFont(ofSize: 20)
        let metaFont = UIFont.systemFont(ofSize: 11)
        let headingFont = UIFont.boldSystemFont(ofSize: 14)
        let bodyFont = UIFont.systemFont(ofSize: 12)

        let titleP = NSMutableParagraphStyle()
        titleP.alignment = .center
        titleP.paragraphSpacing = 12

        let metaP = NSMutableParagraphStyle()
        metaP.lineSpacing = 2
        metaP.paragraphSpacing = 12

        let headingP = NSMutableParagraphStyle()
        headingP.paragraphSpacingBefore = 10
        headingP.paragraphSpacing = 6

        let bodyP = NSMutableParagraphStyle()
        bodyP.lineSpacing = 3
        bodyP.paragraphSpacing = 10

        let doc = NSMutableAttributedString()

        func append(_ text: String, _ attrs: [NSAttributedString.Key: Any]) {
            doc.append(NSAttributedString(string: text, attributes: attrs))
        }

        let originals = payload.segments
            .map { $0.transcription.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: "\n")

        let translations = payload.segments
            .map { $0.translation.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: "\n")

        append(
            "留学宝 实时转译 导出\n",
            [
                .font: titleFont,
                .foregroundColor: UIColor.black,
                .paragraphStyle: titleP,
            ]
        )

        append(
            "exported_at: \(payload.exported_at)\n" +
            "from: \(payload.source_lang)\n" +
            "to: \(payload.target_lang)\n" +
            "api_base_url: \(payload.api_base_url)\n" +
            "segments: \(payload.segments.count)\n\n",
            [
                .font: metaFont,
                .foregroundColor: UIColor.darkGray,
                .paragraphStyle: metaP,
            ]
        )

        append(
            "Original\n",
            [
                .font: headingFont,
                .foregroundColor: UIColor.black,
                .paragraphStyle: headingP,
            ]
        )
        append(
            originals.isEmpty ? "(empty)\n\n" : "\(originals)\n\n",
            [
                .font: bodyFont,
                .foregroundColor: UIColor.black,
                .paragraphStyle: bodyP,
            ]
        )

        append(
            "Translation\n",
            [
                .font: headingFont,
                .foregroundColor: UIColor.black,
                .paragraphStyle: headingP,
            ]
        )
        append(
            translations.isEmpty ? "(empty)\n\n" : "\(translations)\n\n",
            [
                .font: bodyFont,
                .foregroundColor: UIColor.black,
                .paragraphStyle: bodyP,
            ]
        )

        append(
            "Segments\n",
            [
                .font: headingFont,
                .foregroundColor: UIColor.black,
                .paragraphStyle: headingP,
            ]
        )

        let detailFont = UIFont.systemFont(ofSize: 11)
        let detailP = NSMutableParagraphStyle()
        detailP.lineSpacing = 2
        detailP.paragraphSpacing = 8

        for seg in payload.segments.sorted(by: { $0.seq < $1.seq }) {
            var lines: [String] = []
            lines.append("#\(seg.seq)  [\(seg.created_at)]  status=\(seg.status)")
            if let err = seg.error_message, !err.isEmpty {
                lines.append("error: \(err)")
            }
            if !seg.transcription.isEmpty {
                lines.append("original: \(seg.transcription)")
            }
            if !seg.translation.isEmpty {
                lines.append("translation: \(seg.translation)")
            }
            lines.append("")

            append(
                lines.joined(separator: "\n") + "\n",
                [
                    .font: detailFont,
                    .foregroundColor: UIColor.black,
                    .paragraphStyle: detailP,
                ]
            )
        }

        return doc
    }

    private static func suggestedBaseName(
        sourceLang: String,
        targetLang: String,
        exportedAt: Date
    ) -> String {
        let df = DateFormatter()
        df.locale = Locale(identifier: "en_US_POSIX")
        df.timeZone = TimeZone(secondsFromGMT: 0)
        df.dateFormat = "yyyyMMdd-HHmmss'Z'"

        let stamp = df.string(from: exportedAt)
        let base = "interpretation-\(stamp)-\(sourceLang)-\(targetLang)"
        return sanitizeFilename(base)
    }

    private static func sanitizeFilename(_ s: String) -> String {
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_."))  // keep dot for readability
        var out = ""
        var lastWasDash = false
        for scalar in s.unicodeScalars {
            if allowed.contains(scalar) {
                out.append(Character(scalar))
                lastWasDash = false
            } else if !lastWasDash {
                out.append("-")
                lastWasDash = true
            }
        }
        return out.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
    }
}
