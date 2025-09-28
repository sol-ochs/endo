import React from 'react';

interface DisplayFieldProps {
  label: string;
  value: string | undefined;
  className?: string;
}

const DisplayField: React.FC<DisplayFieldProps> = ({ label, value, className = '' }) => {
  return (
    <div className={`field-display ${className}`}>
      <span className="field-label">{label}</span>
      <p className="field-value">{value || 'Not provided'}</p>
    </div>
  );
};

export default DisplayField;