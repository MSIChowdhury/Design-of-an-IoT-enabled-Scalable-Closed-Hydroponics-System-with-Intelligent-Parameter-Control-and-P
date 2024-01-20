% Define the equations
BaseArea = @(W, L, t) (L - 2*t) * (W - 2*t);
SurfaceArea = @(W, L, H) 2 * ((W * H) + (L * H)) + (L * W);

% Define the range of W and L values
W_range = 12:0.1:96;
L_range = 12:0.1:96;

% Create a meshgrid for W and L
[W, L] = meshgrid(W_range, L_range);

% Calculate the corresponding Z values for each equation
Z_BaseArea = BaseArea(W, L, 0.125);
Z_SurfaceArea = SurfaceArea(W, L, 15);

% Plot the two surface plots on the same axes with distinct colors and scales
figure;

subplot(1, 2, 1);
surf(W, L, Z_BaseArea, 'FaceAlpha', 0.8, 'EdgeColor', 'none', 'DisplayName', 'Base Area', 'FaceColor', 'r');
xlabel('W');
ylabel('L');
zlabel('Function Value');
title('3D Surface Plot of Base Area');
legend;
grid on;

subplot(1, 2, 2);
surf(W, L, Z_SurfaceArea, 'FaceAlpha', 0.8, 'EdgeColor', 'none', 'DisplayName', 'Surface Area', 'FaceColor', 'b');
xlabel('W');
ylabel('L');
zlabel('Function Value');
title('3D Surface Plot of Surface Area');
legend;
grid on;