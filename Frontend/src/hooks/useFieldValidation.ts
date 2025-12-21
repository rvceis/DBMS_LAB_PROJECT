import { useState } from 'react';

interface FieldConstraints {
  min?: number;
  max?: number;
  min_length?: number;
  max_length?: number;
  pattern?: string;
  pattern_name?: string;
  enum?: string[];
}

interface FieldDefinition {
  field_name: string;
  field_type: string;
  is_required: boolean;
  constraints?: FieldConstraints;
}

interface ValidationError {
  field: string;
  message: string;
}

export const useFieldValidation = () => {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateField = (
    fieldName: string,
    value: any,
    fieldDef: FieldDefinition
  ): string | null => {
    // Check required
    if (fieldDef.is_required && (value === null || value === '' || value === undefined)) {
      return `${fieldName} is required`;
    }

    // Skip validation for empty non-required fields
    if (!fieldDef.is_required && (value === null || value === '' || value === undefined)) {
      return null;
    }

    const constraints = fieldDef.constraints || {};

    // Type-specific validation
    switch (fieldDef.field_type) {
      case 'string':
        return validateString(fieldName, value, constraints);
      case 'integer':
        return validateInteger(fieldName, value, constraints);
      case 'float':
        return validateFloat(fieldName, value, constraints);
      case 'boolean':
        return validateBoolean(fieldName, value);
      default:
        return null;
    }
  };

  const validateString = (
    fieldName: string,
    value: any,
    constraints: FieldConstraints
  ): string | null => {
    const str = String(value);

    if (constraints.min_length && str.length < constraints.min_length) {
      return `${fieldName} must be at least ${constraints.min_length} characters`;
    }

    if (constraints.max_length && str.length > constraints.max_length) {
      return `${fieldName} must be at most ${constraints.max_length} characters`;
    }

    if (constraints.pattern) {
      try {
        const regex = new RegExp(constraints.pattern);
        if (!regex.test(str)) {
          return `${fieldName} must match ${constraints.pattern_name || 'the required format'}`;
        }
      } catch (e) {
        // Invalid regex, skip
      }
    }

    if (constraints.enum && !constraints.enum.includes(str)) {
      return `${fieldName} must be one of: ${constraints.enum.join(', ')}`;
    }

    return null;
  };

  const validateInteger = (
    fieldName: string,
    value: any,
    constraints: FieldConstraints
  ): string | null => {
    const num = Number(value);

    if (isNaN(num) || !Number.isInteger(num)) {
      return `${fieldName} must be a valid integer`;
    }

    if (constraints.min !== undefined && num < constraints.min) {
      return `${fieldName} must be at least ${constraints.min}`;
    }

    if (constraints.max !== undefined && num > constraints.max) {
      return `${fieldName} must be at most ${constraints.max}`;
    }

    if (constraints.enum && !constraints.enum.map(Number).includes(num)) {
      return `${fieldName} must be one of: ${constraints.enum.join(', ')}`;
    }

    return null;
  };

  const validateFloat = (
    fieldName: string,
    value: any,
    constraints: FieldConstraints
  ): string | null => {
    const num = Number(value);

    if (isNaN(num)) {
      return `${fieldName} must be a valid number`;
    }

    if (constraints.min !== undefined && num < constraints.min) {
      return `${fieldName} must be at least ${constraints.min}`;
    }

    if (constraints.max !== undefined && num > constraints.max) {
      return `${fieldName} must be at most ${constraints.max}`;
    }

    return null;
  };

  const validateBoolean = (fieldName: string, value: any): string | null => {
    if (typeof value === 'boolean') {
      return null;
    }

    if (typeof value === 'string') {
      const lower = value.toLowerCase();
      if (['true', 'false', '1', '0', 'yes', 'no'].includes(lower)) {
        return null;
      }
    }

    return `${fieldName} must be a boolean (true/false)`;
  };

  const validateAll = (
    values: Record<string, any>,
    fields: FieldDefinition[]
  ): Record<string, string> => {
    const newErrors: Record<string, string> = {};

    fields.forEach((field) => {
      const error = validateField(field.field_name, values[field.field_name], field);
      if (error) {
        newErrors[field.field_name] = error;
      }
    });

    setErrors(newErrors);
    return newErrors;
  };

  const clearErrors = () => {
    setErrors({});
  };

  const clearFieldError = (fieldName: string) => {
    setErrors((prev) => {
      const updated = { ...prev };
      delete updated[fieldName];
      return updated;
    });
  };

  return {
    errors,
    validateField,
    validateAll,
    clearErrors,
    clearFieldError,
  };
};
