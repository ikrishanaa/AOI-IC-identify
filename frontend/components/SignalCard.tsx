import type { OCRResult, LogoResult, VisualSignatureResult, AnomalyResult } from "@/types/api";

interface SignalCardProps {
  title: string;
  icon: string;
  data: OCRResult | LogoResult | VisualSignatureResult | AnomalyResult | null;
  type: "ocr" | "logo" | "visual" | "anomaly";
}

export default function SignalCard({ title, icon, data, type }: SignalCardProps) {
  if (!data) {
    return (
      <div className="border border-slate-200 rounded-xl p-5 bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">{icon}</span>
          <h3 className="font-semibold text-slate-400">{title}</h3>
        </div>
        <p className="text-sm text-slate-400">No data available</p>
      </div>
    );
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-emerald-600 font-semibold";
    if (confidence >= 0.6) return "text-amber-600 font-semibold";
    return "text-rose-600 font-semibold";
  };

  const getConfidenceBgColor = (confidence: number) => {
    if (confidence >= 0.8) return "bg-emerald-50 border-emerald-200";
    if (confidence >= 0.6) return "bg-amber-50 border-amber-200";
    return "bg-rose-50 border-rose-200";
  };

  const renderContent = () => {
    switch (type) {
      case "ocr":
        const ocrData = data as OCRResult;
        return (
          <>
            <div className="text-lg font-mono font-bold mb-3 text-slate-800">{ocrData.text}</div>
            <div className={`inline-block px-3 py-1 rounded-full text-sm border ${getConfidenceBgColor(ocrData.confidence)}`}>
              <span className="text-slate-600">Confidence: </span>
              <span className={getConfidenceColor(ocrData.confidence)}>
                {(ocrData.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </>
        );

      case "logo":
        const logoData = data as LogoResult;
        return (
          <>
            <div className="text-lg font-semibold mb-3 text-slate-800">{logoData.manufacturer}</div>
            <div className={`inline-block px-3 py-1 rounded-full text-sm border ${getConfidenceBgColor(logoData.confidence)}`}>
              <span className="text-slate-600">Confidence: </span>
              <span className={getConfidenceColor(logoData.confidence)}>
                {(logoData.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </>
        );

      case "visual":
        const visualData = data as VisualSignatureResult;
        return (
          <>
            <div className={`inline-block px-3 py-1.5 rounded-full text-sm border mb-3 ${getConfidenceBgColor(visualData.similarity)}`}>
              <span className="text-slate-600">Similarity: </span>
              <span className={getConfidenceColor(visualData.similarity)}>
                {(visualData.similarity * 100).toFixed(1)}%
              </span>
            </div>
            {visualData.reference_id && (
              <div className="text-sm text-slate-600 bg-slate-50 px-3 py-1.5 rounded-md">
                <span className="text-slate-500">Ref:</span> <span className="font-mono font-medium">{visualData.reference_id}</span>
              </div>
            )}
          </>
        );

      case "anomaly":
        const anomalyData = data as AnomalyResult;
        const isNormal = !anomalyData.is_anomalous;
        return (
          <>
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-base font-semibold mb-3 border ${
              isNormal 
                ? "bg-emerald-50 text-emerald-700 border-emerald-200" 
                : "bg-rose-50 text-rose-700 border-rose-200"
            }`}>
              {isNormal ? "✓ No Anomalies" : "⚠ Anomaly Detected"}
            </div>
            <div className={`text-sm px-3 py-1.5 rounded-md ${
              isNormal ? "bg-emerald-50" : "bg-rose-50"
            }`}>
              <span className="text-slate-600">Score: </span>
              <span className={`font-semibold ${isNormal ? "text-emerald-600" : "text-rose-600"}`}>
                {(anomalyData.score * 100).toFixed(1)}%
              </span>
            </div>
            {anomalyData.reconstruction_error !== undefined && (
              <div className="text-xs text-slate-500 mt-2 bg-slate-50 px-2 py-1 rounded">
                Reconstruction Error: {anomalyData.reconstruction_error.toFixed(2)}
              </div>
            )}
          </>
        );
    }
  };

  return (
    <div className="border border-slate-200 rounded-xl p-5 bg-white shadow-sm hover:shadow-md transition-all hover:border-blue-300">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">{icon}</span>
        <h3 className="font-semibold text-slate-700">{title}</h3>
      </div>
      {renderContent()}
    </div>
  );
}
