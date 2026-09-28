import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Briefcase, FileText, ArrowRight, Sparkles, Upload, Check } from 'lucide-react';
import { api } from '../api/client';
import { Role } from '../api/types';

export const Roles: React.FC = () => {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [roleFamily, setRoleFamily] = useState('backend');
  const [jdText, setJdText] = useState('');
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: roles, isLoading } = useQuery<Role[]>({
    queryKey: ['roles'],
    queryFn: api.getRoles,
  });

  const createRoleMutation = useMutation({
    mutationFn: async () => {
      if (jdFile) {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('role_family', roleFamily);
        formData.append('file', jdFile);
        return api.createRoleUpload(formData);
      } else {
        return api.createRole(title, jdText, roleFamily);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setShowModal(false);
      setTitle('');
      setJdText('');
      setJdFile(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create role.');
    },
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-white tracking-tight">Open Hiring Roles</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage roles, review extracted competencies, and evaluate candidate readiness.
          </p>
        </div>

        <button
          onClick={() => { setShowModal(true); setError(null); }}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>New Role</span>
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 glass-panel rounded-2xl border border-slate-800" />
          ))}
        </div>
      ) : roles && roles.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {roles.map((role) => (
            <Link
              key={role.role_id}
              to={`/roles/${role.role_id}`}
              className="glass-panel glass-panel-hover rounded-2xl p-6 border border-slate-800 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                    {role.role_family}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {new Date(role.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="font-heading font-semibold text-lg text-white group-hover:text-emerald-400 transition-colors mb-2">
                  {role.title}
                </h3>

                <div className="space-y-1.5 my-4">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Key Competencies ({role.competencies?.length || 0}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {role.competencies?.slice(0, 3).map((c, i) => (
                      <span
                        key={i}
                        className="text-xs bg-slate-800/80 text-slate-300 px-2 py-0.5 rounded border border-slate-700/60 line-clamp-1"
                      >
                        {c.name}
                      </span>
                    ))}
                    {(role.competencies?.length || 0) > 3 && (
                      <span className="text-xs text-slate-500 self-center">
                        +{(role.competencies?.length || 0) - 3} more
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 group-hover:text-slate-300">
                <span>View Candidates & Results</span>
                <ArrowRight className="w-4 h-4 text-emerald-400 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 glass-panel rounded-3xl border border-slate-800 space-y-4">
          <Briefcase className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-lg font-heading font-semibold text-white">No roles created yet</h3>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            Create your first role to parse competencies and start screening candidates.
          </p>
        </div>
      )}

      {/* Create Role Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel max-w-2xl w-full p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center space-x-2.5">
                <Sparkles className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl font-heading font-bold text-white">Create New Role</h2>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                Cancel
              </button>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                {error}
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                setError(null);
                createRoleMutation.mutate();
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Job Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Senior Backend Engineer"
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Role Family</label>
                  <select
                    value={roleFamily}
                    onChange={(e) => setRoleFamily(e.target.value)}
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="backend">Backend</option>
                    <option value="frontend">Frontend</option>
                    <option value="ml">Machine Learning</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">
                  Job Description Text or File Upload
                </label>
                <textarea
                  rows={6}
                  value={jdText}
                  onChange={(e) => { setJdText(e.target.value); setJdFile(null); }}
                  placeholder="Paste complete Job Description here..."
                  className="w-full bg-slate-950/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="text-center text-xs text-slate-500 font-semibold">— OR UPLOAD DOCUMENT —</div>

              <div className="flex items-center space-x-3">
                <label className="flex-1 flex items-center justify-center space-x-2 border-2 border-dashed border-slate-800 hover:border-emerald-500/40 rounded-xl p-3 cursor-pointer transition-colors bg-slate-900/40">
                  <Upload className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-slate-300">
                    {jdFile ? jdFile.name : 'Upload JD (PDF, DOCX, TXT)'}
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setJdFile(e.target.files[0]);
                        setJdText('');
                      }
                    }}
                    className="hidden"
                  />
                </label>
                {jdFile && (
                  <button
                    type="button"
                    onClick={() => setJdFile(null)}
                    className="text-xs text-rose-400 hover:text-rose-300"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 text-[11px] text-slate-400 flex items-start space-x-2">
                <Sparkles className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span>
                  Creating a role triggers a single small-model LLM call to extract and rank competencies.
                  This analysis is amortized across all candidates for this role.
                </span>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createRoleMutation.isPending || (!jdText.trim() && !jdFile)}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-heading font-bold text-xs shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                >
                  {createRoleMutation.isPending ? 'Extracting Competencies...' : 'Create & Parse Role'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
