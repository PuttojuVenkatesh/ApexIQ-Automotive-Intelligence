import { useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  FileText,
  LockKeyhole,
  LogOut,
  RefreshCw,
  Trash2,
  Upload,
} from 'lucide-react';
import {
  deleteBrochure,
  getBrochurePdf,
  getDocuments,
  loginAdmin,
  logoutAdmin,
  uploadBrochure,
} from '../services/api';

const pendingStatuses = new Set(['uploaded', 'processing']);

export default function BrochureAdminSection() {
  const [adminToken, setAdminToken] = useState(() => sessionStorage.getItem('apexiq_admin_token') || '');
  const [adminUsername, setAdminUsername] = useState(() => sessionStorage.getItem('apexiq_admin_username') || '');
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [documents, setDocuments] = useState([]);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const clearAdminSession = () => {
    sessionStorage.removeItem('apexiq_admin_token');
    sessionStorage.removeItem('apexiq_admin_username');
    setAdminToken('');
    setAdminUsername('');
    setDocuments([]);
  };

  const showAdminError = (error) => {
    setMessage({ type: 'error', text: error.message });
    if (error.status === 401) clearAdminSession();
  };

  const refreshDocuments = async (token = adminToken) => {
    if (!token) return;
    setIsLoading(true);
    try {
      const result = await getDocuments(token);
      setDocuments(result.documents || []);
    } catch (error) {
      showAdminError(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (adminToken) refreshDocuments(adminToken);
  }, [adminToken]);

  useEffect(() => {
    if (!adminToken || !documents.some((document) => pendingStatuses.has(document.status))) return undefined;
    const timer = window.setInterval(() => refreshDocuments(adminToken), 3000);
    return () => window.clearInterval(timer);
  }, [adminToken, documents]);

  const handleLogin = async (event) => {
    event.preventDefault();
    try {
      const result = await loginAdmin(usernameInput.trim(), passwordInput);
      sessionStorage.setItem('apexiq_admin_token', result.access_token);
      sessionStorage.setItem('apexiq_admin_username', result.username);
      setAdminUsername(result.username);
      setPasswordInput('');
      setMessage({ type: 'success', text: 'Administrator verified.' });
      setAdminToken(result.access_token);
    } catch (error) {
      showAdminError(error);
    }
  };

  const handleLogout = async () => {
    let logoutError;
    try {
      await logoutAdmin(adminToken);
    } catch (error) {
      logoutError = error;
    }
    clearAdminSession();
    setMessage(logoutError && logoutError.status !== 401
      ? { type: 'error', text: `Signed out of this browser, but server sign-out could not be confirmed: ${logoutError.message}` }
      : { type: 'success', text: 'Administrator signed out.' });
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setMessage({ type: 'error', text: 'Choose a PDF brochure.' });
      return;
    }
    try {
      setMessage({ type: 'info', text: `Uploading ${file.name}...` });
      const result = await uploadBrochure(file, adminToken);
      setMessage({ type: 'success', text: result.message });
      await refreshDocuments();
    } catch (error) {
      showAdminError(error);
    }
  };

  const handleView = async (document) => {
    const popup = window.open('about:blank', '_blank');
    if (!popup) {
      setMessage({ type: 'error', text: 'Allow pop-ups to open the brochure.' });
      return;
    }
    try {
      const pdf = await getBrochurePdf(document.id, adminToken);
      popup.location.href = URL.createObjectURL(pdf);
    } catch (error) {
      popup.close();
      showAdminError(error);
    }
  };

  const handleDelete = async (document) => {
    if (!window.confirm(`Remove ${document.filename} and its indexed brochure content?`)) return;
    try {
      const result = await deleteBrochure(document.id, adminToken);
      setMessage({ type: 'success', text: result.message });
      await refreshDocuments();
    } catch (error) {
      showAdminError(error);
    }
  };

  const statusLabel = (status) => ({
    indexed: 'Ready',
    processing: 'Processing',
    uploaded: 'Queued',
    failed: 'Needs attention',
  }[status] || status || 'Unknown');

  return (
    <main className="min-h-screen bg-[#f2f0ea] text-[#171719] px-5 pt-32 pb-20 sm:px-8">
      <div className="max-w-6xl mx-auto">
        <a href="#models" className="text-xs font-bold uppercase tracking-[0.16em] text-[#65645e] hover:text-black">
          Back to ApexIQ
        </a>
        <div className="mt-8 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#77766f]">ApexIQ administration</p>
            <h1 className="mt-3 text-4xl sm:text-5xl font-black tracking-[-0.04em]">Brochure library</h1>
            <p className="mt-4 max-w-2xl text-[#65645e] leading-7">
              Add official vehicle brochures and manage the documents used to answer GearGuide questions.
            </p>
            {adminToken && (
              <p className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-green-800">
                <CheckCircle2 className="h-4 w-4" /> Administrator verified: {adminUsername}
              </p>
            )}
          </div>
          {adminToken && (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => refreshDocuments()}
                disabled={isLoading}
                className="inline-flex items-center gap-2 border border-[#bdbbb3] px-4 py-3 text-xs font-bold uppercase tracking-wider hover:border-black disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
              </button>
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center gap-2 border border-[#bdbbb3] px-4 py-3 text-xs font-bold uppercase tracking-wider hover:border-black"
              >
                <LogOut className="h-4 w-4" /> Sign out
              </button>
              <label className="inline-flex cursor-pointer items-center gap-2 bg-[#171719] px-5 py-3 text-xs font-bold uppercase tracking-wider text-white hover:bg-black">
                <Upload className="h-4 w-4" /> Add brochure
                <input type="file" accept="application/pdf,.pdf" onChange={handleUpload} className="hidden" />
              </label>
            </div>
          )}
        </div>

        {!adminToken && (
          <form onSubmit={handleLogin} className="mt-10 max-w-xl border border-[#d1cec5] bg-white p-6 sm:p-8">
            <LockKeyhole className="h-6 w-6" />
            <h2 className="mt-4 text-xl font-bold">Administrator access</h2>
            <p className="mt-2 text-sm leading-6 text-[#65645e]">
              Sign in with the administrator ID and password configured for the backend. Your verified session is kept in this browser tab.
            </p>
            <div className="mt-5 flex flex-col gap-3">
              <input
                type="text"
                autoComplete="username"
                required
                value={usernameInput}
                onChange={(event) => setUsernameInput(event.target.value)}
                placeholder="Administrator ID"
                className="min-w-0 border border-[#bdbbb3] px-4 py-3 text-sm outline-none focus:border-black"
              />
              <input
                type="password"
                autoComplete="current-password"
                required
                value={passwordInput}
                onChange={(event) => setPasswordInput(event.target.value)}
                placeholder="Password"
                className="min-w-0 border border-[#bdbbb3] px-4 py-3 text-sm outline-none focus:border-black"
              />
              <button className="bg-[#171719] px-5 py-3 text-xs font-bold uppercase tracking-wider text-white">
                Verify administrator
              </button>
            </div>
          </form>
        )}

        {message && (
          <div className={`mt-6 flex items-start gap-3 border p-4 text-sm ${
            message.type === 'error' ? 'border-red-300 bg-red-50 text-red-800'
              : message.type === 'success' ? 'border-green-300 bg-green-50 text-green-800'
                : 'border-blue-300 bg-blue-50 text-blue-800'
          }`}>
            {message.type === 'success' ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              : message.type === 'info' ? <RefreshCw className="mt-0.5 h-4 w-4 shrink-0 animate-spin" />
                : <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />}
            <span>{message.text}</span>
          </div>
        )}

        {adminToken && (
          <div className="mt-10 overflow-hidden border border-[#d1cec5] bg-white">
            <div className="border-b border-[#e4e1da] px-5 py-4 text-xs font-bold uppercase tracking-[0.16em] text-[#77766f]">
              {documents.length} {documents.length === 1 ? 'brochure' : 'brochures'}
            </div>
            {documents.length === 0 ? (
              <div className="p-10 text-center text-[#65645e]">No brochures are available yet.</div>
            ) : (
              <div className="divide-y divide-[#e4e1da]">
                {documents.map((document) => (
                  <article key={document.id} className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex min-w-0 items-start gap-4">
                      <FileText className="mt-1 h-5 w-5 shrink-0 text-[#77766f]" />
                      <div className="min-w-0">
                        <h2 className="break-all font-bold">{document.filename}</h2>
                        <p className="mt-1 text-sm text-[#65645e]">
                          {[document.brand, document.model].filter(Boolean).join(' ') || 'Vehicle brochure'}
                          {document.page_count ? ` | ${document.page_count} pages` : ''}
                          {document.file_size_bytes ? ` | ${(document.file_size_bytes / 1048576).toFixed(1)} MB` : ''}
                        </p>
                        {document.status === 'failed' && document.error_message && (
                          <p className="mt-2 text-sm text-red-700">{document.error_message}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <span className={`text-xs font-bold uppercase tracking-wider ${
                        document.status === 'failed' ? 'text-red-700'
                          : document.status === 'indexed' ? 'text-green-700' : 'text-[#77766f]'
                      }`}>
                        {statusLabel(document.status)}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleView(document)}
                        title="View brochure"
                        aria-label={`View ${document.filename}`}
                        className="border border-[#d1cec5] p-2 hover:border-black"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(document)}
                        title="Remove brochure"
                        aria-label={`Remove ${document.filename}`}
                        className="border border-[#d1cec5] p-2 text-red-700 hover:border-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
