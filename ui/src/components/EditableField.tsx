import React from 'react';

interface EditableFieldProps {
  label: string;
  name: string;
  type?: string;
  value: string;
  onChange: (name: string, value: string) => void;
  required?: boolean;
  className?: string;
}

const EditableField: React.FC<EditableFieldProps> = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  required = false,
  className = ''
}) => {
  return (
    <div className={`form-group ${className}`}>
      <label className="form-label">{label}</label>
      <input
        type={type}
        className="form-input"
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        required={required}
      />
    </div>
  );
};

export default EditableField;