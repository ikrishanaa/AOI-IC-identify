"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function NewInspectionPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [fileName, setFileName] = useState<string>("");
  const [imageData, setImageData] = useState<string>("");
  const [componentType, setComponentType] = useState<string>("IC");
  const [referenceId, setReferenceId] = useState<string>("REF-001");
  const [batchId, setBatchId] = useState<string>("");

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setFileName(file.name);
    
    // Convert to base64 (in production, upload to object storage first)
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      setImageData(base64);
    };
    reader.readAsDataURL(file);
  };

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    
    if (!imageData) {
      alert("Please select an image");
      return;
    }
    
    setSubmitting(true);
    try {
      const payload = {
        image_data: imageData,
        component_type: componentType,
        reference_id: referenceId,
        metadata: batchId ? { batch: batchId } : {},
      };
      
      const r = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      const body = await r.json();
      
      if (r.ok && body?.job_id) {
        router.push(`/inspections/${body.job_id}`);
      } else {
        alert(`Error: ${body.error || "Failed to create inspection"}`);
      }
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-slate-800">New Batch Inspection</h1>
      
      <form onSubmit={onSubmit} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
        {/* Image Upload */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Component Image *
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition-colors"
            required
          />
          {fileName && (
            <p className="mt-2 text-sm text-emerald-600 font-medium">✓ Selected: {fileName}</p>
          )}
        </div>

        {/* Component Type */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Component Type
          </label>
          <select
            value={componentType}
            onChange={(e) => setComponentType(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-slate-700"
          >
            <option value="IC">Integrated Circuit (IC)</option>
            <option value="PCB">Printed Circuit Board</option>
            <option value="Resistor">Resistor</option>
            <option value="Capacitor">Capacitor</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Reference ID */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Reference Component ID
          </label>
          <input
            type="text"
            value={referenceId}
            onChange={(e) => setReferenceId(e.target.value)}
            placeholder="REF-001"
            className="block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700"
          />
          <p className="mt-1 text-xs text-slate-500">
            Optional: Compare against a reference golden sample
          </p>
        </div>

        {/* Batch ID */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Batch ID (Optional)
          </label>
          <input
            type="text"
            value={batchId}
            onChange={(e) => setBatchId(e.target.value)}
            placeholder="BATCH-2025-001"
            className="block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700"
          />
          <p className="mt-1 text-xs text-slate-500">
            Group related inspections together
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting || !imageData}
            className="flex-1 bg-blue-600 text-white py-2.5 px-4 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            {submitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Submitting...
              </span>
            ) : (
              "Start Inspection"
            )}
          </button>
          <button
            type="button"
            onClick={() => router.push("/")}
            className="px-4 py-2.5 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <span className="text-xl">ℹ️</span>
          How it works
        </h3>
        <ul className="text-sm text-blue-800 space-y-1.5">
          <li>• Your image is analyzed using 4 verification signals</li>
          <li>• OCR extracts text from the component</li>
          <li>• Logo detection identifies the manufacturer</li>
          <li>• Visual signature compares against reference samples</li>
          <li>• Anomaly detection checks for tampering</li>
          <li>• Decision engine fuses all signals for final verdict</li>
        </ul>
      </div>
    </section>
  );
}
