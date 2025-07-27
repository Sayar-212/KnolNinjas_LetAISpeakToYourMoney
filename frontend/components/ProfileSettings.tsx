import React, { useState, useEffect } from 'react';
import { UserCircleIcon, LogoutIcon, NotificationIcon, SettingsIcon, ChevronRightIcon, PencilIcon, CheckIcon, CloseIcon } from './IconComponents';

interface ProfileSettingsProps {
    onLogout: () => void;
    user: any;
}

const ACCENT_COLORS = [
    { name: 'Cyan', value: '34 211 238' },
    { name: 'Rose', value: '244 63 94' },
    { name: 'Amber', value: '245 158 11' },
    { name: 'Lime', value: '132 204 22' },
    { name: 'Violet', value: '139 92 246' },
];

const ChangePasswordModal: React.FC<{onClose: () => void}> = ({ onClose }) => (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" onClick={onClose}>
        <div className="bg-[#1e1f22] p-8 rounded-2xl w-full max-w-md shadow-2xl border border-zinc-700" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold text-white">Change Password</h3>
                <button onClick={onClose} className="text-zinc-500 hover:text-white"><CloseIcon className="w-6 h-6"/></button>
            </div>
            <form className="space-y-4">
                 <div>
                    <label className="text-sm font-medium text-zinc-400">Current Password</label>
                    <input type="password" className="mt-1 w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-md focus:outline-none focus:ring-2 ring-accent" />
                </div>
                <div>
                    <label className="text-sm font-medium text-zinc-400">New Password</label>
                    <input type="password" className="mt-1 w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-md focus:outline-none focus:ring-2 ring-accent" />
                </div>
                <div>
                    <label className="text-sm font-medium text-zinc-400">Confirm New Password</label>
                    <input type="password" className="mt-1 w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-md focus:outline-none focus:ring-2 ring-accent" />
                </div>
                <div className="pt-4 flex justify-end gap-3">
                    <button type="button" onClick={onClose} className="px-4 py-2 rounded-md text-white font-semibold bg-zinc-600 hover:bg-zinc-500 transition-colors">Cancel</button>
                    <button type="submit" className="px-4 py-2 rounded-md text-white font-semibold bg-accent hover:opacity-90 transition-colors">Save Changes</button>
                </div>
            </form>
        </div>
    </div>
);

const SettingsRow: React.FC<{ icon: React.ElementType, label: string, onClick?: () => void, children?: React.ReactNode }> = ({ icon: Icon, label, onClick, children }) => (
    <button onClick={onClick} disabled={!onClick && !children} className="w-full flex items-center justify-between p-4 bg-zinc-700/50 rounded-lg hover:bg-zinc-700 transition-colors disabled:cursor-default disabled:hover:bg-zinc-700/50">
        <div className="flex items-center gap-4">
            <Icon className="w-6 h-6 text-zinc-400" />
            <span className="text-white font-medium">{label}</span>
        </div>
        <div>
            {children || (onClick && <ChevronRightIcon className="w-5 h-5 text-zinc-500" />)}
        </div>
    </button>
);

const ToggleSwitch: React.FC<{checked: boolean; onChange: () => void}> = ({ checked, onChange }) => {
    return (
        <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" value="" className="sr-only peer" checked={checked} onChange={onChange} />
            <div className="w-11 h-6 bg-zinc-600 rounded-full peer peer-focus:ring-2 ring-accent peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
        </label>
    );
}

const ProfileSettings: React.FC<ProfileSettingsProps> = ({ onLogout, user }) => {
    const [name, setName] = useState(user?.displayName || 'User');
    const [email, setEmail] = useState(user?.email || 'No email');
    
    // Update state when user prop changes
    useEffect(() => {
        setName(user?.displayName || 'User');
        setEmail(user?.email || 'No email');
        setTempName(user?.displayName || 'User');
        setTempEmail(user?.email || 'No email');
    }, [user]);
    const [tempName, setTempName] = useState(name);
    const [tempEmail, setTempEmail] = useState(email);
    const [isEditing, setIsEditing] = useState(false);
    
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);
    const [showSavedNotice, setShowSavedNotice] = useState(false);
    
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    
    const [activeColor, setActiveColor] = useState(ACCENT_COLORS[0].value);

    useEffect(() => {
        document.documentElement.style.setProperty('--color-accent-rgb', activeColor);
    }, [activeColor]);

    const handleSaveProfile = () => {
        setName(tempName);
        setEmail(tempEmail);
        setIsEditing(false);
        showSavedNotification();
    };

    const showSavedNotification = () => {
        setShowSavedNotice(true);
        setTimeout(() => setShowSavedNotice(false), 2000);
    };

    return (
        <div className="max-w-4xl mx-auto text-white relative">
             {showSavedNotice && (
                <div className="fixed top-24 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg transition-all animate-bounce">
                    Settings saved!
                </div>
            )}
            {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}

            <div className="bg-zinc-800/50 p-8 rounded-2xl mb-6">
                <div className="flex flex-col sm:flex-row items-center gap-6">
                    {user?.photoURL ? (
                        <img src={user.photoURL} alt="Profile" className="w-24 h-24 rounded-full object-cover shrink-0" />
                    ) : (
                        <div className="w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white text-2xl font-bold shrink-0">
                            {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                        </div>
                    )}
                    <div className="flex-grow text-center sm:text-left">
                        {isEditing ? (
                            <div className="flex flex-col gap-2">
                                <input type="text" value={tempName} onChange={e => setTempName(e.target.value)} className="text-3xl font-bold bg-zinc-700 rounded-md px-2 py-1 focus:outline-none focus:ring-2 ring-accent"/>
                                <input type="email" value={tempEmail} onChange={e => setTempEmail(e.target.value)} className="text-zinc-400 bg-zinc-700 rounded-md px-2 py-1 focus:outline-none focus:ring-2 ring-accent"/>
                            </div>
                        ) : (
                             <div>
                                <h2 className="text-3xl font-bold">{name}</h2>
                                <p className="text-zinc-400 mt-1">{email}</p>
                            </div>
                        )}
                    </div>
                     <button onClick={() => isEditing ? handleSaveProfile() : setIsEditing(true)} className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold bg-zinc-700 hover:bg-zinc-600 transition-colors">
                        {isEditing ? <CheckIcon className="w-5 h-5"/> : <PencilIcon className="w-5 h-5"/>}
                        {isEditing ? 'Save' : 'Edit Profile'}
                    </button>
                </div>
            </div>

            <div className="bg-zinc-800/50 p-8 rounded-2xl">
                <h3 className="text-xl font-semibold mb-6">Settings</h3>
                <div className="space-y-4">
                    <SettingsRow icon={NotificationIcon} label="Email Notifications">
                        <ToggleSwitch checked={notificationsEnabled} onChange={() => { setNotificationsEnabled(p => !p); showSavedNotification(); }} />
                    </SettingsRow>
                    <SettingsRow icon={SettingsIcon} label="Account Settings" onClick={() => setShowPasswordModal(true)} />
                    <SettingsRow icon={SettingsIcon} label="Appearance">
                        <div className="flex gap-2">
                            {ACCENT_COLORS.map(color => (
                                <button key={color.name} title={color.name} onClick={() => { setActiveColor(color.value); showSavedNotification(); }} className={`w-6 h-6 rounded-full transition-all ${activeColor === color.value ? 'ring-2 ring-offset-2 ring-offset-zinc-700 ring-white' : ''}`} style={{ backgroundColor: `rgb(${color.value})`}} />
                            ))}
                        </div>
                    </SettingsRow>
                </div>
                
                <div className="mt-8 pt-8 border-t border-zinc-700">
                     <button
                        onClick={onLogout}
                        className="w-full max-w-xs flex items-center justify-center gap-3 py-3 px-4 rounded-lg transition-colors text-white font-semibold bg-red-600/80 hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-zinc-800"
                    >
                        <LogoutIcon className="w-6 h-6" />
                        <span>Sign Out</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProfileSettings;