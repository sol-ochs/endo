import React, { useState, useEffect } from 'react';
import authService from '../services/auth';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { ApiError } from '../types';
import DisplayField from './DisplayField';
import EditableField from './EditableField';

interface ProfileForm {
  first_name: string;
  last_name: string;
  email: string;
}

const ProfileSection: React.FC = () => {
  const { user, updateUser } = useAuth();
  const { addToast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [profileForm, setProfileForm] = useState<ProfileForm>({
    first_name: '',
    last_name: '',
    email: ''
  });

  useEffect(() => {
    if (user) {
      setProfileForm({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email
      });
    }
  }, [user]);

  if (!user) {
    return null;
  }

  const handleFieldChange = (name: string, value: string) => {
    setProfileForm(prev => ({ ...prev, [name]: value }));
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setProfileForm({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email
    });
  };

  const handleSave = async () => {
    try {
      const changes: Partial<ProfileForm> = {};
      if (profileForm.first_name !== user.first_name) {
        changes.first_name = profileForm.first_name;
      }
      if (profileForm.last_name !== user.last_name) {
        changes.last_name = profileForm.last_name;
      }
      if (profileForm.email !== user.email) {
        changes.email = profileForm.email;
      }

      const updatedUserData = await authService.updateProfile(changes);
      updateUser(updatedUserData);
      setIsEditing(false);
      addToast('Profile updated successfully!', 'success');
    } catch (err) {
      const error = err as ApiError;
      addToast(error.message || 'Failed to update profile. Please try again.', 'error');
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Account Profile</h2>
        <p className="card-description">
          Manage your account information and preferences.
        </p>
      </div>

      {isEditing ? (
        <div>
          <div className="field-section--columns">
            <EditableField
              label="First Name"
              name="first_name"
              value={profileForm.first_name}
              onChange={handleFieldChange}
              required
            />
            <EditableField
              label="Last Name"
              name="last_name"
              value={profileForm.last_name}
              onChange={handleFieldChange}
              required
            />
            <EditableField
              label="Email"
              name="email"
              type="email"
              value={profileForm.email}
              onChange={handleFieldChange}
              required
            />
          </div>
          <div className="button-group">
            <button onClick={handleSave} className="btn btn-primary">
              Save Changes
            </button>
            <button onClick={handleCancel} className="btn btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div className="field-section--columns">
            <DisplayField label="First Name" value={user.first_name} />
            <DisplayField label="Last Name" value={user.last_name} />
            <DisplayField label="Email" value={user.email} />
            <DisplayField
              label="Member Since"
              value={user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
            />
          </div>
          <button onClick={handleEdit} className="btn btn-primary btn-single">
            Edit Profile
          </button>
        </div>
      )}
    </div>
  );
};

export default ProfileSection;