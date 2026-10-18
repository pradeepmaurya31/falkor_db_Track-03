import React, { useEffect, useMemo, useState } from 'react';
import ChatDrawer from './ChatDrawer';

const defaultDashboard = {
  user: { name: '', email: '', role: '', status: 'ACTIVE' },
  permissions: [],
  summary: { cards: [] },
  admins: [],
  managers: [],
  employees: [],
  projects: [],
  tickets: [],
  attendance: [],
  holidays: [],
  access_controls: {},
};

const badgeClasses = {
  SuperAdmin: 'bg-purple-100 text-purple-700',
  Admin: 'bg-indigo-100 text-indigo-700',
  Manager: 'bg-amber-100 text-amber-700',
  Employee: 'bg-emerald-100 text-emerald-700',
};

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('enterprise_token') || null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('');
  const [dashboard, setDashboard] = useState(defaultDashboard);
  const [loading, setLoading] = useState(false);
  const [showPermissions, setShowPermissions] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);

  const recordAttendance = async (sessionToken, action) => {
    try {
      await fetch(`http://localhost:8000/api/attendance/${action}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${sessionToken}`,
        },
      });
    } catch (error) {
      console.warn(`Attendance ${action} update failed:`, error);
    }
  };

  const fetchDashboard = async (sessionToken) => {
    const res = await fetch('http://localhost:8000/api/dashboard', {
      headers: {
        Authorization: `Bearer ${sessionToken}`,
      },
    });

    if (!res.ok) {
      throw new Error('Unable to load dashboard data');
    }

    const data = await res.json();
    setDashboard(data);
    setRole(data.user.role);
  };

  useEffect(() => {
    if (token) {
      localStorage.setItem('enterprise_token', token);
      fetchDashboard(token).catch((error) => {
        console.error(error);
        alert('Failed to load dashboard. Please sign in again.');
        setToken(null);
      });
      recordAttendance(token, 'clock-in');
      return;
    }
    localStorage.removeItem('enterprise_token');
  }, [token]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || 'Login failed');
        return;
      }

      setToken(data.access_token);
      await recordAttendance(data.access_token, 'clock-in');
      setRole(data.role || 'Employee');
    } catch (error) {
      console.error(error);
      alert('Unable to connect to the backend. Start the Python API on port 8000 first.');
    } finally {
      setLoading(false);
    }
  };

  const userName = dashboard?.user?.name || (email || 'User');
  const roleTitle = useMemo(() => `${role || 'User'} Dashboard`, [role]);
  const currentUserEmail = dashboard?.user?.email || email;
  const myAttendance = useMemo(() => {
    const explicitMyAttendance = Array.isArray(dashboard?.my_attendance) ? dashboard.my_attendance : [];
    if (explicitMyAttendance.length) return explicitMyAttendance;
    if (!currentUserEmail) return [];
    return (dashboard.attendance || []).filter(
      (entry) => String(entry.user_email || '').toLowerCase() === String(currentUserEmail).toLowerCase()
    );
  }, [dashboard, currentUserEmail]);

  useEffect(() => {
    document.title = 'Maurya Corporation';
  }, []);

  const refreshDashboard = async () => {
    if (!token) return;
    try {
      await fetchDashboard(token);
    } catch (error) {
      console.error(error);
      alert('Failed to refresh dashboard.');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      alert('Please fill in all password fields.');
      return;
    }
    if (newPassword !== confirmPassword) {
      alert('New password and confirm password must match.');
      return;
    }
    if (newPassword.length < 8) {
      alert('New password must be at least 8 characters long.');
      return;
    }

    setPasswordLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Password update failed');
      }
      alert('Password updated successfully.');
      setShowPasswordModal(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error(error);
      alert(error.message || 'Unable to update password.');
    } finally {
      setPasswordLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-100">
        <form onSubmit={handleLogin} className="bg-white p-8 rounded-2xl shadow-lg w-[420px] space-y-4">
          <div className="text-center space-y-3">
            <div className="rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 px-5 py-4 shadow-md">
              <p className="text-3xl font-black tracking-wide text-white">Maurya Corporation</p>
            </div>
            <h2 className="text-2xl font-bold text-slate-800">Secure login</h2>
          </div>

          <div className="space-y-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-label="Email"
              className="w-full border border-slate-200 rounded-xl px-3 py-3 outline-none focus:border-blue-500"
              required
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-label="Password"
              className="w-full border border-slate-200 rounded-xl px-3 py-3 outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold disabled:opacity-60"
          >
            {loading ? 'Signing in...' : 'Login'}
          </button>
        </form>
      </div>
    );
  }

  const summaryCards = dashboard.summary?.cards || [];

  return (
    <div className="flex h-screen bg-slate-100 mr-96">
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-800">Change password</h3>
              <button type="button" onClick={() => setShowPasswordModal(false)} className="text-slate-500">✕</button>
            </div>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Current password"
                className="w-full border border-slate-200 rounded-xl px-3 py-3 outline-none focus:border-blue-500"
                required
              />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="New password"
                className="w-full border border-slate-200 rounded-xl px-3 py-3 outline-none focus:border-blue-500"
                required
              />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="w-full border border-slate-200 rounded-xl px-3 py-3 outline-none focus:border-blue-500"
                required
              />
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowPasswordModal(false)} className="rounded-xl border border-slate-200 px-4 py-2 text-sm">Cancel</button>
                <button type="submit" disabled={passwordLoading} className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
                  {passwordLoading ? 'Updating...' : 'Update password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="flex-1 p-6 overflow-y-auto">
        <header className="mb-6 flex items-center justify-between gap-4 px-0 py-0">
          <div className="flex-1 min-w-0">
            <div className="text-left">
              <h1 className="text-4xl md:text-5xl font-black tracking-[0.12em] text-blue-700 uppercase leading-none break-words">
                Maurya Corporation
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0 pt-2">
            <button
              type="button"
              onClick={refreshDashboard}
              className="border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 rounded-xl hover:bg-slate-50"
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => setShowPasswordModal(true)}
              className="bg-slate-100 text-slate-800 px-4 py-2 rounded-xl text-sm font-medium border border-slate-200"
            >
              Change password
            </button>
            <button
              type="button"
              onClick={async () => {
                if (token) {
                  await recordAttendance(token, 'clock-out');
                }
                setToken(null);
                localStorage.removeItem('enterprise_token');
              }}
              className="bg-slate-800 text-white px-4 py-2 rounded-xl text-sm font-medium"
            >
              Sign out
            </button>
          </div>
        </header>

        <div className="mb-4 mt-[-8px] flex items-center justify-between gap-4">
          <div>
            <div className="text-sm font-medium text-slate-500 uppercase tracking-[0.18em]">{(dashboard.user.role || role || 'User').toUpperCase()}</div>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-800 leading-tight">Welcome {userName}</h2>
          </div>
          <div className="hidden md:inline-flex items-center rounded-full px-3 py-1 text-xs font-medium text-slate-600 bg-slate-200/80">
            {dashboard.user.role || role}
          </div>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          {summaryCards.map((card) => (
            <div key={card.label} className="bg-white rounded-2xl shadow-sm p-4 border border-slate-100">
              <p className="text-sm text-slate-500">{card.label}</p>
              <h3 className="mt-2 text-3xl font-bold text-slate-800">{card.value}</h3>
            </div>
          ))}
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-1 gap-6 mb-6">
          <div className="bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <div className="flex w-full items-center justify-between text-left">
              <h2 className="text-lg font-bold text-slate-800">Permissions</h2>
              <button
                type="button"
                onClick={() => setShowPermissions((prev) => !prev)}
                className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600"
              >
                {showPermissions ? 'Hide' : 'View'}
              </button>
            </div>

            {showPermissions && (
              <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 shadow-inner">
                <div className="flex flex-wrap gap-2">
                  {(dashboard.permissions || []).map((permission) => (
                    <span key={permission} className="rounded-full bg-blue-50 text-blue-700 px-3 py-1 text-xs font-medium">{permission}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>

        {role && !['Employee'].includes(String(role)) && (
          <section className="mb-6 bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">My Attendance</h2>
            <div className="space-y-3">
              {myAttendance.length ? (
                myAttendance.slice(0, 5).map((entry) => (
                  <div key={entry.id} className="border rounded-xl p-3 bg-slate-50">
                    <p className="font-medium text-slate-700">{entry.user_email}</p>
                    <p className="text-xs text-slate-500">{entry.date} · {entry.in_time} to {entry.out_time}</p>
                    <p className="text-xs text-slate-500">{entry.type} · {entry.is_leave ? 'Leave' : 'Present'}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No attendance record available for your account yet.</p>
              )}
            </div>
          </section>
        )}

        <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">People</h2>
            <div className="space-y-3">
              {(dashboard.admins || []).map((user) => (
                <div key={user.email} className="flex justify-between items-center border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium text-slate-700">{user.name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  <span className="text-xs rounded-full bg-slate-100 px-2 py-1">{user.role}</span>
                </div>
              ))}
              {(dashboard.managers || []).map((user) => (
                <div key={user.email} className="flex justify-between items-center border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium text-slate-700">{user.name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  <span className="text-xs rounded-full bg-slate-100 px-2 py-1">{user.role}</span>
                </div>
              ))}
              {(dashboard.employees || []).map((user) => (
                <div key={user.email} className="flex justify-between items-center border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium text-slate-700">{user.name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  <span className="text-xs rounded-full bg-slate-100 px-2 py-1">{user.role}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Projects</h2>
            <div className="space-y-3">
              {(dashboard.projects || []).map((project) => (
                <div key={project.id} className="border rounded-xl p-3 bg-slate-50">
                  <div className="flex justify-between items-center">
                    <p className="font-semibold text-slate-700">{project.name}</p>
                    <span className="text-xs rounded-full bg-emerald-100 text-emerald-700 px-2 py-1">{project.status}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Client: {project.client_name}</p>
                  <p className="text-xs text-slate-500">Cost: ${project.cost}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Employee Attendance</h2>
            <div className="space-y-3">
              {(dashboard.attendance || []).slice(0, 5).map((entry) => (
                <div key={entry.id} className="border rounded-xl p-3 bg-slate-50">
                  <p className="font-medium text-slate-700">{entry.user_email}</p>
                  <p className="text-xs text-slate-500">{entry.date} · {entry.in_time} to {entry.out_time}</p>
                  <p className="text-xs text-slate-500">{entry.type} · {entry.is_leave ? 'Leave' : 'Present'}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-6 grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Tickets</h2>
            <div className="space-y-3">
              {(dashboard.tickets || []).map((ticket) => (
                <div key={ticket.id} className="border rounded-xl p-3 bg-slate-50">
                  <div className="flex justify-between items-center">
                    <p className="font-medium text-slate-700">{ticket.type}</p>
                    <span className="text-xs rounded-full bg-amber-100 text-amber-700 px-2 py-1">{ticket.status}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">{ticket.comments}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm p-5 border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Holidays</h2>
            <div className="space-y-3">
              {(dashboard.holidays || []).map((holiday) => (
                <div key={holiday.id} className="flex justify-between items-center border rounded-xl p-3 bg-slate-50 gap-3">
                  <div>
                    <p className="font-medium text-slate-700">{holiday.holiday_name}</p>
                    <p className="text-xs text-slate-500">{holiday.holiday_type}</p>
                    <p className="text-xs text-slate-500">{holiday.holiday_date || holiday.year}</p>
                  </div>
                  <span className="text-xs rounded-full bg-sky-100 text-sky-700 px-2 py-1 whitespace-nowrap">{holiday.year}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      <ChatDrawer token={token} />
    </div>
  );
}