import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useMemo } from 'react';
import { useUIStore } from '@/stores/uiStore';

export const useAppTheme = () => {
  const theme = useUIStore((state) => state.theme);

  return useMemo(() => {
    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    const commonPalette = {
      primary: {
        main: '#6366F1',
        light: '#818CF8',
        dark: '#4F46E5',
      },
      secondary: {
        main: '#10B981',
        light: '#34D399',
        dark: '#059669',
      },
      success: {
        main: '#10B981',
        light: '#34D399',
      },
      warning: {
        main: '#F59E0B',
      },
      error: {
        main: '#EF4444',
      },
      info: {
        main: '#3B82F6',
      },
    };

    return createTheme({
      palette: {
        mode: isDark ? 'dark' : 'light',
        ...commonPalette,
        ...(isDark
          ? {
              background: {
                default: '#0F172A',
                paper: '#1E293B',
              },
              surface: '#334155',
              text: {
                primary: '#F1F5F9',
                secondary: '#CBD5E1',
                disabled: '#64748B',
              },
            }
          : {
              background: {
                default: '#F8FAFC',
                paper: '#FFFFFF',
              },
              surface: '#F1F5F9',
              text: {
                primary: '#0F172A',
                secondary: '#475569',
                disabled: '#94A3B8',
              },
            }),
      },
      typography: {
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        h1: {
          fontSize: '2rem',
          fontWeight: 700,
          letterSpacing: '-0.02em',
        },
        h2: {
          fontSize: '1.5rem',
          fontWeight: 700,
          letterSpacing: '-0.01em',
        },
        h3: {
          fontSize: '1.25rem',
          fontWeight: 600,
        },
        h4: {
          fontSize: '1.125rem',
          fontWeight: 600,
        },
        body1: {
          fontSize: '0.95rem',
          lineHeight: 1.6,
        },
        body2: {
          fontSize: '0.875rem',
          lineHeight: 1.5,
        },
      },
      shape: {
        borderRadius: 8,
      },
      components: {
        MuiButton: {
          styleOverrides: {
            root: {
              textTransform: 'none',
              fontWeight: 600,
              fontSize: '0.95rem',
              borderRadius: 8,
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 16px rgba(99, 102, 241, 0.2)',
              },
            },
            contained: {
              background: 'linear-gradient(135deg, #6366F1 0%, #10B981 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #4F46E5 0%, #059669 100%)',
              },
            },
          },
        },
        MuiCard: {
          styleOverrides: {
            root: {
              borderRadius: 12,
              backdropFilter: 'blur(10px)',
              backgroundColor: isDark ? 'rgba(30, 41, 59, 0.7)' : 'rgba(255, 255, 255, 0.7)',
              border: isDark ? '1px solid rgba(71, 85, 105, 0.3)' : '1px solid rgba(241, 245, 249, 0.3)',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                boxShadow: isDark
                  ? '0 20px 40px rgba(0, 0, 0, 0.3)'
                  : '0 20px 40px rgba(0, 0, 0, 0.08)',
              },
            },
          },
        },
        MuiPaper: {
          styleOverrides: {
            root: {
              backgroundImage: 'none',
            },
          },
        },
        MuiTextField: {
          styleOverrides: {
            root: {
              '& .MuiOutlinedInput-root': {
                borderRadius: 8,
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  borderColor: '#6366F1',
                },
              },
            },
          },
        },
        MuiChip: {
          styleOverrides: {
            root: {
              borderRadius: 6,
              fontWeight: 500,
            },
          },
        },
      },
    });
  }, [theme]);
};

export const AppThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const appTheme = useAppTheme();

  return (
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};
