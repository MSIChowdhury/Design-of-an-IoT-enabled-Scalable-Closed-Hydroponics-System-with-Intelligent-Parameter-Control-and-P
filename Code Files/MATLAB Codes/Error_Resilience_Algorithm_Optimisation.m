% This script optimizes alpha and beta parameters for multiple sensors using a cost function approach.
% It uses random initializations and a gradient descent-like method to find optimal parameters.
% Multiple learning rates are tested to find the best performance.

% Initialize variables to store the best results
best_total_cost_function_value = Inf;
best_combination_total_cost_function_values = [];
best_weight_combination = [];

% Initialize table to store all weight combinations and their cost values
all_weight_combinations = [];

% Initialize table to store all alpha, beta combinations and their cost values
all_sensor_cost_data = table();

% Define the optimization parameters and stopping criteria
alpha_threshold = 1e-6;  % Convergence threshold for alpha
beta_threshold = 1e-6;   % Convergence threshold for beta
min_iterations = 1000;   % Minimum number of iterations before checking convergence
cost_threshold = 1e-6;   % Convergence threshold for cost function
alpha_max = 1.00;        % Maximum value for alpha
beta_max = 1.00;         % Maximum value for beta
min_stable_values = 1000;  % Number of consecutive stable values required for convergence

% Define sensor columns to be processed
sensor_columns = {'EC', 'pH', 'Air_Temp', 'Water_Temp', 'Water_Level', 'CO2'};
num_sensors = length(sensor_columns);

% Start the timer to measure total execution time
tic;

% Load the sensor data from CSV file
filename = 'C:\Users\SAMEER\Sensor Data First Trial.csv';
data = readtable(filename);

% Define lower and upper bounds for each sensor
L_lower_values = [900, 5.8, 20, 18, 8, 1900];
L_upper_values = [1300, 6.5, 26, 22, 15, 2100];

num_initializations = 10;  % Number of random initializations

% Define the learning rates to test
lr_step = 0.001;
lr_start = lr_step;
lr_end = 1 - lr_step;
lr_values = lr_start:lr_step:lr_end;

% Initialize arrays to store results for each learning rate
total_costs = zeros(size(lr_values));
best_alphas = cell(size(lr_values));
best_betas = cell(size(lr_values));

% Create figure and plot objects for real-time plotting
figure;
h = plot(NaN, NaN, 'b-', 'LineWidth', 2);
xlabel('Learning Rate');
ylabel('Total Cost Function Value');
title('Total Cost Function vs Learning Rate (Real-time)');
grid on;
xlim('auto');
ylim('auto');

% Initialize table to store results for CSV
results_table = table('Size', [0, num_sensors + 2], 'VariableTypes', ['double', repmat({'double'}, 1, num_sensors + 1)]);
results_table.Properties.VariableNames = ['LearningRate', sensor_columns, 'TotalCost'];

% Main loop for different learning rates
for lr_idx = 1:length(lr_values)
    lr = lr_values(lr_idx);
    fprintf('Processing with learning rate: %.3f\n', lr);

    % Initialize best overall results for this learning rate
    global_best_alpha = zeros(length(sensor_columns), 1);
    global_best_beta = zeros(length(sensor_columns), 1);
    global_best_error_counter = zeros(length(sensor_columns), 1);
    global_best_cost = Inf * ones(length(sensor_columns), 1);

    % Initialize array to store best total cost history
    best_total_cost_history = [];

    for init = 1:num_initializations
        fprintf('Initialization %d/%d\n', init, num_initializations);

        % Initialize alpha and beta arrays for each sensor column with random values
        alpha_values = 0.01 + 0.98 * rand(length(sensor_columns), 1);
        beta_values = 0.01 + 0.98 * rand(length(sensor_columns), 1);
        fprintf('Initial alpha values: %s\n', num2str(alpha_values'));
        fprintf('Initial beta values: %s\n', num2str(beta_values'));

        % Initialize best values for alpha and beta
        best_alpha_values = zeros(length(sensor_columns), 1);
        best_beta_values = zeros(length(sensor_columns), 1);

        % Initialize error counters
        total_error_counter = 0;
        total_sensor_readings = 0;

        % Initialize best overall results for this initialization
        best_overall_alpha = zeros(length(sensor_columns), 1);
        best_overall_beta = zeros(length(sensor_columns), 1);
        best_overall_error_counter = zeros(length(sensor_columns), 1);
        best_overall_cost = zeros(length(sensor_columns), 1);

        % Initialize total cost history for this initialization
        total_cost_history = [];

        % Loop over each sensor column
        for col_idx = 1:length(sensor_columns)
            fprintf('Processing column: %s\n', sensor_columns{col_idx});
            
            % Select the current column in the CSV file
            sensor_values = data.(sensor_columns{col_idx});
            
            % Calculate xi (average absolute difference between consecutive sensor values)
            M = length(sensor_values);
            delta_sensor = abs(diff(sensor_values));
            xi = sum(delta_sensor) / M;
            fprintf('xi = %.4f\n', xi);
            
            % Calculate psi (average length of consecutive values within 2*xi threshold)
            abs_diff_within_threshold = abs(delta_sensor) <= 2 * xi;
            consecutive_groups = diff([0; abs_diff_within_threshold(:); 0]);
            start_indices = find(consecutive_groups == 1);
            end_indices = find(consecutive_groups == -1);
            sequence_lengths = end_indices - start_indices + 1;
            if ~isempty(sequence_lengths)
                average_length = mean(sequence_lengths);
            else
                average_length = 0;
            end
            psi = floor(average_length);
            fprintf('psi = %d\n', psi);
            
            % Compute historical mean and variance of sensor values
            mu_V = mean(sensor_values);
            sigma_V_squared = var(sensor_values);
            fprintf('mu_V = %.4f\n', mu_V);
            fprintf('sigma_V_squared = %.4f\n', sigma_V_squared);
            
            % Initialize lambda values (weights for cost function components)
            lambda_alpha = 1;
            lambda_beta = 1;
            lambda_E = 1;

            % Initialize cost function values
            [total_error_counts, ~] = computeErrorCounts(sensor_values, alpha_values(col_idx), beta_values(col_idx), xi, L_lower_values(col_idx), L_upper_values(col_idx));
            normalized_error = total_error_counts / M;
            
            normalized_alpha = (alpha_values(col_idx)/alpha_max);
            normalized_beta = (beta_values(col_idx)/beta_max);
            
            c1 = lambda_E * normalized_error + lambda_alpha * normalized_alpha + lambda_beta + normalized_beta;
            c2 = c1;  % Initial cost (will be updated in the optimization loop)

            % Initialize flags for convergence check
            converged = false;
            iteration_count = 0;
            stable_count = 0;
            
            % Optimize alpha and beta
            while ~converged
                alpha_old = alpha_values(col_idx);
                beta_old = beta_values(col_idx);
                
                % Calculate the cost ratio
                cost_ratio = c1 / c2;
                
                % Update alpha and beta using a gradient descent-like approach
                alpha_new = alpha_values(col_idx) * (1 - lr * (log(cost_ratio) + (lr/max(iteration_count, 1))));
                beta_new = beta_values(col_idx) * (1 - lr * (log(cost_ratio) + (lr/max(iteration_count, 1))));
                
                % Update lambda values (weights for cost function components)
                lambda_alpha = lambda_alpha * (1 - abs(log(cost_ratio)));
                lambda_beta = lambda_beta * (1 - abs(log(cost_ratio)));
                lambda_E = lambda_E * (1 + abs(log(cost_ratio)));
                
                normalized_alpha_new = (alpha_new/alpha_max);
                normalized_beta_new = (beta_new/beta_max);
                
                % Compute new cost for updated alpha and beta
                [total_error_counts_new, ~] = computeErrorCounts(sensor_values, alpha_new, beta_new, xi, L_lower_values(col_idx), L_upper_values(col_idx));
                normalized_error_new = total_error_counts_new / M;
                c1 = lambda_E * normalized_error_new + lambda_alpha * normalized_alpha_new + lambda_beta * normalized_beta_new;
                
                % Update total cost history
                total_cost_history = [total_cost_history; c1];
                
                % Check for convergence after minimum iterations
                if iteration_count >= min_iterations
                    if abs(alpha_new - alpha_old) < alpha_threshold && abs(beta_new - beta_old) < beta_threshold && abs(c1 - c2) < cost_threshold
                        stable_count = stable_count + 1;
                        if stable_count >= min_stable_values
                            converged = true;
                        end
                    else
                        stable_count = 0;
                    end
                end
                
                % Update alpha and beta values
                alpha_values(col_idx) = alpha_new;
                beta_values(col_idx) = beta_new;
                
                fprintf('At Lr = %.3f, Iteration %d for Initialization %d/%d for %s: alpha: %.10f, beta: %.10f, cost: %.10f\n',lr, iteration_count, init, num_initializations, sensor_columns{col_idx}, alpha_new, beta_new, c1);
                
                iteration_count = iteration_count + 1;
                
                % Update c2 for the next iteration
                c2 = c1;
            end
            
            % Store the best alpha and beta values for this sensor
            best_alpha_values(col_idx) = alpha_values(col_idx);
            best_beta_values(col_idx) = beta_values(col_idx);
            
            % Update best overall results for this sensor column
            best_overall_alpha(col_idx) = alpha_values(col_idx);
            best_overall_beta(col_idx) = beta_values(col_idx);
            best_overall_error_counter(col_idx) = total_error_counts_new;
            best_overall_cost(col_idx) = c1;
        end

        % Update global best results
        for col_idx = 1:length(sensor_columns)
            if best_overall_cost(col_idx) < global_best_cost(col_idx)
                global_best_alpha(col_idx) = best_overall_alpha(col_idx);
                global_best_beta(col_idx) = best_overall_beta(col_idx);
                global_best_error_counter(col_idx) = best_overall_error_counter(col_idx);
                global_best_cost(col_idx) = best_overall_cost(col_idx);
            end
        end

        % Update best total cost history
        if isempty(best_total_cost_history)
            best_total_cost_history = total_cost_history;
        else
            best_total_cost_history = min(best_total_cost_history(1:min(length(best_total_cost_history), length(total_cost_history))), ...
                                          total_cost_history(1:min(length(best_total_cost_history), length(total_cost_history))));
            if length(total_cost_history) > length(best_total_cost_history)
                best_total_cost_history = [best_total_cost_history; total_cost_history(length(best_total_cost_history)+1:end)];
            end
        end
    end

    % Calculate total cost for this learning rate
    total_cost = sum(global_best_cost);
    
    % Store results for this learning rate
    total_costs(lr_idx) = total_cost;
    best_alphas{lr_idx} = global_best_alpha;
    best_betas{lr_idx} = global_best_beta;

    % Update the plot
    set(h, 'XData', lr_values(1:lr_idx), 'YData', total_costs(1:lr_idx));
    xlim('auto');
    ylim('auto');
    drawnow;  % Force MATLAB to update the plot

    % Add results to the table
    new_row = [lr, global_best_cost', total_cost];
    results_table = [results_table; array2table(new_row, 'VariableNames', results_table.Properties.VariableNames)];
end

% Find the best learning rate
[best_total_cost, best_lr_idx] = min(total_costs);
best_lr = lr_values(best_lr_idx);
best_alpha = best_alphas{best_lr_idx};
best_beta = best_betas{best_lr_idx};

% Display the best results
fprintf('\nBest overall results:\n');
fprintf('Best learning rate: %.3f\n', best_lr);
fprintf('Sum of lowest costs: %.6f\n', best_total_cost);

for col_idx = 1:length(sensor_columns)
    fprintf('Sensor: %s\n', sensor_columns{col_idx});
    fprintf('  Best alpha: %.6f\n', best_alpha(col_idx));
    fprintf('  Best beta: %.6f\n', best_beta(col_idx));
    fprintf('  Best cost: %.6f\n', global_best_cost(col_idx));
    fprintf('  Best error counter: %d\n', global_best_error_counter(col_idx));
    fprintf('\n');
end

% Stop the timer and display elapsed time
elapsed_time = toc;
hours = floor(elapsed_time / 3600);
minutes = floor((elapsed_time - hours * 3600) / 60);
seconds = elapsed_time - hours * 3600 - minutes * 60;
fprintf('Total time elapsed: %02d:%02d:%05.2f\n', hours, minutes, seconds);

% Save results to CSV file
writetable(results_table, 'C:\Users\SAMEER\optimization_results (resolution = 0.001).csv');
fprintf('Results saved to optimization_results (resolution = 0.001).csv\n');

% Helper function to compute error counts
function [total_error_counts, VT] = computeErrorCounts(sensor_values, alpha, beta, xi, L_lower, L_upper)
    M = length(sensor_values);
    error_counter_matrix = zeros(M, 1);
    VT = sensor_values(1);  % Initialize VT with the first sensor value
    
    for n = 2:M
        Vn = sensor_values(n);
        
        % Check if the sensor value is outside the acceptable range
        if Vn > (L_upper + alpha * xi) * 1.10 || Vn < (L_lower - alpha * xi) * 0.90
            error_counter_matrix(n) = 1;  % Error if exceeding zeta bounds by more than 10%
        else
            error_counter_matrix(n) = 0;  % No error
        end
        
        % Update VT if the new value is within the acceptable range
        if abs(Vn - VT) <= (1 + beta) * xi
            VT = Vn;
        end
    end
    
    % Calculate total error counts
    total_error_counts = sum(error_counter_matrix);
end