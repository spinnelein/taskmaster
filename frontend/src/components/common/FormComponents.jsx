// Enhanced form components with responsive grid and progressive disclosure
// NO EMOJIS
import { useState } from 'react';
import './FormComponents.css';

// Responsive Form Grid
export function FormGrid({ children, columns = [1, 2, 3], gap = '16px', className = '' }) {
  const gridStyle = {
    '--grid-columns-mobile': columns[0] || 1,
    '--grid-columns-tablet': columns[1] || columns[0] || 1, 
    '--grid-columns-desktop': columns[2] || columns[1] || columns[0] || 1,
    '--grid-gap': gap
  };

  return (
    <div 
      className={`form-grid ${className}`}
      style={gridStyle}
    >
      {children}
    </div>
  );
}

// Form Field with enhanced styling
export function FormField({ 
  label, 
  required = false, 
  error, 
  helpText, 
  children, 
  className = '',
  fullWidth = false 
}) {
  return (
    <div className={`form-field ${fullWidth ? 'form-field-full' : ''} ${className}`}>
      {label && (
        <label className="form-label">
          {label}
          {required && <span className="form-required">*</span>}
        </label>
      )}
      
      <div className="form-input-wrapper">
        {children}
      </div>
      
      {error && <div className="form-error">{error}</div>}
      {helpText && !error && <div className="form-help">{helpText}</div>}
    </div>
  );
}

// Collapsible Form Section with progressive disclosure
export function FormSection({ 
  title, 
  children, 
  collapsible = false, 
  defaultExpanded = true,
  icon = null,
  className = ''
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const toggleSection = () => {
    if (collapsible) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className={`form-section ${className}`}>
      <div 
        className={`form-section-header ${collapsible ? 'form-section-header-clickable' : ''}`}
        onClick={toggleSection}
        role={collapsible ? 'button' : undefined}
        tabIndex={collapsible ? 0 : undefined}
        onKeyDown={collapsible ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleSection();
          }
        } : undefined}
      >
        {icon && <span className="form-section-icon">{icon}</span>}
        <h3 className="form-section-title">{title}</h3>
        {collapsible && (
          <svg 
            className={`form-section-chevron ${isExpanded ? 'expanded' : ''}`}
            width="20" 
            height="20" 
            viewBox="0 0 20 20" 
            fill="none"
          >
            <path 
              d="M6 8L10 12L14 8" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        )}
      </div>
      
      <div className={`form-section-content ${collapsible && !isExpanded ? 'collapsed' : ''}`}>
        {(!collapsible || isExpanded) && children}
      </div>
    </div>
  );
}

// Enhanced Text Input
export function TextInput({ 
  type = 'text', 
  placeholder, 
  value, 
  onChange, 
  disabled = false,
  autoComplete,
  className = '',
  ...props 
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      autoComplete={autoComplete}
      className={`form-input ${disabled ? 'form-input-disabled' : ''} ${className}`}
      {...props}
    />
  );
}

// Enhanced Select
export function Select({ 
  value, 
  onChange, 
  options = [], 
  placeholder = 'Select an option',
  disabled = false,
  className = '',
  ...props 
}) {
  return (
    <select
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={`form-select ${disabled ? 'form-select-disabled' : ''} ${className}`}
      {...props}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((option, index) => (
        <option key={index} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

// Enhanced Textarea
export function Textarea({ 
  value, 
  onChange, 
  rows = 3, 
  placeholder,
  disabled = false,
  autoResize = false,
  className = '',
  ...props 
}) {
  const handleChange = (e) => {
    if (autoResize) {
      e.target.style.height = 'auto';
      e.target.style.height = `${e.target.scrollHeight}px`;
    }
    onChange?.(e);
  };

  return (
    <textarea
      value={value}
      onChange={handleChange}
      rows={rows}
      placeholder={placeholder}
      disabled={disabled}
      className={`form-textarea ${disabled ? 'form-textarea-disabled' : ''} ${className}`}
      {...props}
    />
  );
}

// Priority Matrix Component (replaces simple priority input)
export function PriorityMatrix({ value, onChange, className = '' }) {
  const priorities = [
    { value: 1, label: 'Low', color: '#10b981' },
    { value: 3, label: 'Medium', color: '#f59e0b' },
    { value: 5, label: 'High', color: '#ef4444' },
    { value: 7, label: 'Urgent', color: '#dc2626' },
    { value: 10, label: 'Critical', color: '#7c2d12' }
  ];

  return (
    <div className={`priority-matrix ${className}`}>
      {priorities.map((priority) => (
        <button
          key={priority.value}
          type="button"
          onClick={() => onChange?.({ target: { value: priority.value } })}
          className={`priority-btn ${value === priority.value ? 'priority-btn-active' : ''}`}
          style={{
            '--priority-color': priority.color,
            backgroundColor: value === priority.value ? priority.color : 'transparent',
            borderColor: priority.color,
            color: value === priority.value ? 'white' : priority.color
          }}
        >
          {priority.label}
        </button>
      ))}
    </div>
  );
}

// Quick Duration Selector
export function DurationSelect({ value, onChange, className = '' }) {
  const durations = [
    { value: 15, label: '15m' },
    { value: 30, label: '30m' },
    { value: 45, label: '45m' },
    { value: 60, label: '1h' },
    { value: 90, label: '1.5h' },
    { value: 120, label: '2h' },
    { value: 180, label: '3h' },
    { value: 240, label: '4h' }
  ];

  return (
    <div className={`duration-select ${className}`}>
      <div className="duration-buttons">
        {durations.map((duration) => (
          <button
            key={duration.value}
            type="button"
            onClick={() => onChange?.({ target: { value: duration.value } })}
            className={`duration-btn ${value === duration.value ? 'duration-btn-active' : ''}`}
          >
            {duration.label}
          </button>
        ))}
      </div>
      
      <div className="duration-custom">
        <TextInput
          type="number"
          value={value}
          onChange={onChange}
          min="1"
          max="480"
          placeholder="Custom minutes"
        />
      </div>
    </div>
  );
}

// Form Actions with consistent spacing
export function FormActions({ children, className = '', alignment = 'right' }) {
  return (
    <div className={`form-actions form-actions-${alignment} ${className}`}>
      {children}
    </div>
  );
}

// Enhanced Button components
export function Button({ 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  loading = false,
  children, 
  className = '',
  ...props 
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`btn btn-${variant} btn-${size} ${disabled ? 'btn-disabled' : ''} ${loading ? 'btn-loading' : ''} ${className}`}
      {...props}
    >
      {loading && (
        <svg className="btn-spinner" width="16" height="16" viewBox="0 0 24 24">
          <circle 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="2" 
            fill="none"
            strokeDasharray="31.416"
            strokeDashoffset="31.416"
          />
        </svg>
      )}
      {children}
    </button>
  );
}

export function SecondaryButton({ children, ...props }) {
  return <Button variant="secondary" {...props}>{children}</Button>;
}

export function CancelButton({ children, ...props }) {
  return <Button variant="cancel" {...props}>{children}</Button>;
}