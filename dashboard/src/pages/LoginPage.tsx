import { useEffect, useState } from 'react';
import { ShieldCheck, Sun, Moon, ChevronDown, LogIn, Users } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../hooks/useTheme';
import { useApiCall } from '../hooks/useApiCall';
import { listPolicyRoles, listUsers } from '../api/queryvault';
import { PolicyRoleSummary, PolicyRolesResponse } from '../types/policies';
import { User, UsersResponse } from '../types/users';
import { LoadingSpinner } from '../components/shared/LoadingSpinner';
import {
  DOMAIN_GROUP_LABELS,
  DOMAIN_GROUP_TEXT_COLORS,
  DOMAIN_ICON,
  CLEARANCE_BADGE,
} from '../constants/userCategories';

function formatRoleName(name: string): string {
  return name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

function groupRolesByDomain(roles: PolicyRoleSummary[]): Record<string, PolicyRoleSummary[]> {
  return roles.reduce<Record<string, PolicyRoleSummary[]>>((acc, role) => {
    const domain = role.domain || 'OTHER';
    if (!acc[domain]) acc[domain] = [];
    acc[domain].push(role);
    return acc;
  }, {});
}



export function LoginPage() {
  const { login, loading: loginLoading } = useAuth();
  const { isDark, toggle } = useTheme();
  const { loading: loadingRoles, result: rolesResult, execute: fetchRoles } = useApiCall<PolicyRolesResponse>();
  const { loading: loadingUsers, result: usersResult, execute: fetchUsers } = useApiCall<UsersResponse>();

  const [selectedRole, setSelectedRole] = useState<PolicyRoleSummary | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  useEffect(() => {
    fetchRoles(() => listPolicyRoles());
    fetchUsers(() => listUsers());
  }, []);

  useEffect(() => {
    if (!dropdownOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('#role-dropdown-container')) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [dropdownOpen]);

  const allRoles = rolesResult?.data?.roles ?? [];
  const users = usersResult?.data?.users ?? [];

  const configuredRoles = allRoles.filter((r) => {
    const name = r.name.toUpperCase();
    return (
      (r.domain === 'CLINICAL' && name === 'ATTENDING_PHYSICIAN') ||
      (r.domain === 'FINANCIAL' && name === 'BILLING_CLERK') ||
      (r.domain === 'HR' && name === 'HR_MANAGER')
    );
  });

  const roleUserMap = new Map<string, User>();
  for (const user of users) {
    for (const role of user.ad_roles) {
      if (!roleUserMap.has(role)) roleUserMap.set(role, user);
    }
  }

  const grouped = groupRolesByDomain(configuredRoles);

  const handleLogin = async () => {
    if (!selectedRole) return;
    const user = roleUserMap.get(selectedRole.name);
    if (!user) return;
    setLoginError(null);
    setIsLoggingIn(true);
    try {
      await login(user);
    } catch (err: any) {
      setLoginError(err.message ?? 'Login failed');
      setIsLoggingIn(false);
    }
  };

  const isLoading = loadingRoles || loadingUsers;
  const loadError = rolesResult?.error || usersResult?.error;
  const selectedUser = selectedRole ? roleUserMap.get(selectedRole.name) : null;
  const selectedBadge = selectedRole ? CLEARANCE_BADGE[selectedRole.clearance_level] : null;
  const DomainIcon = selectedRole ? (DOMAIN_ICON[selectedRole.domain] ?? Users) : null;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 text-center">
      {/* Soft background glow layers */}
      <div className="absolute top-[-100px] left-[-100px] w-[300px] h-[300px] bg-indigo-400/15 blur-3xl rounded-full pointer-events-none" style={{ animation: 'slowPulse 8s ease-in-out infinite' }} />
      <div className="absolute bottom-[-100px] right-[-100px] w-[300px] h-[300px] bg-blue-400/15 blur-3xl rounded-full pointer-events-none" style={{ animation: 'slowPulse 8s ease-in-out infinite 4s' }} />

      {/* Theme toggle */}
      <button
        onClick={toggle}
        className="absolute top-5 right-5 z-20 p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all"
        aria-label="Toggle theme"
      >
        {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>

      {/* Card */}
      <div
        className="relative z-10 w-full max-w-md mx-4 group"
        style={{ animation: 'fadeSlideUp 0.5s ease both' }}
      >
        {/* Glow effect behind card */}
        <div className="absolute -inset-2 bg-indigo-500/10 blur-2xl rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        <style>{`
          @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
          }
          @keyframes slowPulse {
            0%, 100% { opacity: 0.4; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
          }
        `}</style>

        {/* Logo + Title */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 mb-4 shadow-sm">
            <ShieldCheck className="w-7 h-7 text-indigo-600" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-600 to-blue-500 bg-clip-text text-transparent pb-1">
            Apollo Hospitals
          </h1>
          <p className="text-sm text-indigo-500/80 font-semibold mt-1 tracking-wide uppercase">AI Query Security Demo</p>
        </div>

        {/* Card body - Dark Glass Premium Theme */}
        <div className="relative bg-[#0F172A]/90 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-xl hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-500 hover:scale-[1.01]">
          <p className="text-sm text-slate-300/90 text-center mb-6 leading-relaxed">
            Select a role to access the system. Each role enforces different clearance
            levels, domain access, and data visibility policies.
          </p>

          {loginError && (
            <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400">
              {loginError}
            </div>
          )}

          {loadError && (
            <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400">
              Failed to load roles: {loadError}
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center gap-2 py-8 text-gray-400">
              <LoadingSpinner size={18} />
              <span className="text-sm">Loading roles...</span>
            </div>
          ) : (
            <>
              {/* Dropdown */}
              <div className="mb-4" id="role-dropdown-container">
                <label className="block text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">
                  Select Role
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setDropdownOpen((prev) => !prev)}
                    disabled={loginLoading || isLoggingIn}
                    className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-[#0a2a4a] bg-[#040f1e] hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-black/20"
                  >
                    {selectedRole ? (
                      <span className="flex items-center gap-2.5">
                        {DomainIcon && (
                          <DomainIcon
                            className={`w-4 h-4 flex-shrink-0 ${DOMAIN_GROUP_TEXT_COLORS[selectedRole.domain] ?? 'text-gray-400'}`}
                          />
                        )}
                        <span className="text-sm font-medium text-white">
                          {formatRoleName(selectedRole.name)}
                        </span>
                      </span>
                    ) : (
                      <span className="text-sm text-slate-300/70">Choose a role...</span>
                    )}
                    <ChevronDown
                      className={`w-4 h-4 text-slate-500/50 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`}
                    />
                  </button>

                  {dropdownOpen && (
                    <div className="absolute z-50 w-full mt-2 bg-[#040f1e] border border-[#0a2a4a] rounded-xl shadow-2xl overflow-hidden max-h-72 overflow-y-auto ring-1 ring-black/50">
                      {Object.entries(grouped).map(([domain, domainRoles]) => {
                        const Icon = DOMAIN_ICON[domain] ?? Users;
                        const textColor = DOMAIN_GROUP_TEXT_COLORS[domain] ?? 'text-gray-400';
                        const domainLabel = DOMAIN_GROUP_LABELS[domain] ?? domain;
                        return (
                          <div key={domain}>
                            <div className="flex items-center gap-1.5 px-4 py-2 bg-[#020B18] border-b border-[#0a2a4a] sticky top-0">
                              <Icon className={`w-3 h-3 ${textColor}`} />
                              <span className={`text-[10px] font-bold uppercase tracking-widest ${textColor}`}>
                                {domainLabel}
                              </span>
                            </div>
                            {domainRoles.map((role) => {
                              const hasUser = roleUserMap.has(role.name);
                              const badge = CLEARANCE_BADGE[role.clearance_level] ?? CLEARANCE_BADGE[1];
                              const isSelected = selectedRole?.name === role.name;
                              return (
                                <button
                                  key={role.name}
                                  type="button"
                                  disabled={!hasUser}
                                  onClick={() => {
                                    setSelectedRole(role);
                                    setDropdownOpen(false);
                                    setLoginError(null);
                                  }}
                                  className={`w-full flex items-center justify-between px-4 py-2.5 text-left transition-colors
                                    ${isSelected
                                      ? 'bg-indigo-900/40 text-indigo-300'
                                      : hasUser
                                        ? 'hover:bg-[#0a1f35] text-slate-300'
                                        : 'opacity-40 cursor-not-allowed text-slate-500'
                                    }`}
                                >
                                  <span className="text-sm font-medium">{formatRoleName(role.name)}</span>
                                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${badge.color}`}>
                                    {badge.label}
                                  </span>
                                </button>
                              );
                            })}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Selected role info */}
              {selectedRole && (
                <div
                  className="mb-5 p-4 rounded-xl border border-indigo-500/20 bg-[#020617]/60"
                  style={{ animation: 'fadeSlideUp 0.2s ease both' }}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <p className="text-sm font-semibold text-indigo-50">{formatRoleName(selectedRole.name)}</p>
                      {selectedUser && (
                        <p className="text-xs text-slate-400 mt-0.5">
                          Signing in as{' '}
                          <span className="text-indigo-400 font-medium">{selectedUser.display_name}</span>
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                      {selectedBadge && (
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${selectedBadge.color}`}>
                          {selectedBadge.label}
                        </span>
                      )}
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-900/40 text-indigo-300 border border-indigo-500/20">
                        {selectedRole.domain}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[10px] uppercase font-bold tracking-wider text-slate-500">
                    {selectedRole.allowed_tables.length > 0 && (
                      <span className="flex items-center gap-1.5 bg-green-500/10 text-green-400 px-2 py-0.5 rounded-md border border-green-500/20">
                        <span className="w-1 h-1 rounded-full bg-green-400" />
                        {selectedRole.allowed_tables.length} Tables
                      </span>
                    )}
                    {selectedRole.denied_operations.length > 0 && (
                      <span className="flex items-center gap-1.5 bg-red-500/10 text-red-400 px-2 py-0.5 rounded-md border border-red-500/20">
                        <span className="w-1 h-1 rounded-full bg-red-400" />
                        {selectedRole.denied_operations.length} Denied
                      </span>
                    )}
                    {!selectedUser && (
                      <span className="text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">No user assigned</span>
                    )}
                  </div>
                </div>
              )}

              {/* Login button */}
              <button
                type="button"
                onClick={handleLogin}
                disabled={!selectedRole || !selectedUser || loginLoading || isLoggingIn}
                className="w-full flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl font-semibold tracking-wide text-sm transition-all duration-300
                  bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700
                  text-white shadow-lg shadow-indigo-500/25 hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:scale-[1.02] active:scale-[0.98]
                  disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100 disabled:shadow-none"
              >
                {isLoggingIn ? (
                  <>
                    <LoadingSpinner size={16} />
                    Signing in...
                  </>
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    Sign In
                  </>
                )}
              </button>
            </>
          )}
        </div>

        <p className="text-center text-xs text-gray-500 mt-6 tracking-wide opacity-80">
          Apollo Hospitals · AI Query Security Platform
        </p>
      </div>
    </div>
  );
}
//changes