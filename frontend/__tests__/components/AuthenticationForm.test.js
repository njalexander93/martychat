import { render, screen } from '@testing-library/react';
import AuthenticationForm from '@/components/AuthenticationForm';

describe('AuthenticationForm', () => {
  test('renders children inside the form', () => {
    render(
      <AuthenticationForm>
        <div data-testid="test-child">Test Child</div>
      </AuthenticationForm>
    );

    // Check if the child was rendered
    expect(screen.getByTestId('test-child')).toBeInTheDocument();
    expect(screen.getByText('Test Child')).toBeInTheDocument();
  });

  test('displays logo and authentication form container', () => {
    render(
      <AuthenticationForm>
        <div>Content</div>
      </AuthenticationForm>
    );

    // Check if the logo is rendered
    const logo = screen.getByAltText('MartyChat Logo');
    expect(logo).toBeInTheDocument();

    // Check if the form container exists
    const formContainer = screen.getByRole('link', { name: /martychat logo/i }).closest('div');
    expect(formContainer).toBeInTheDocument();
  });
});
