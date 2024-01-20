% Step 1: Declare variables
H = 15;
t = 0.125;
tolerance = 0.1;  % Set the tolerance to 10%

% Step 2: Declare Rounder function
Rounder = @(x) round(x);

% Step 3: Maximizer for Base Area
BaseArea = @(W, L, t) (L - 2*t) * (W - 2*t);
maximizerBaseArea = @(x) -BaseArea(x(1), x(2), t);

% Step 4: Minimizer for Volume
Volume = @(W, L, H) W * L * H;
minimizerVolume = @(x) Volume(x(1), x(2), H);

% Step 5: Minimizer for Surface Area of Material Used
SurfaceArea = @(W, L, H) 2 * ((W * H) + (L * H)) + (L * W);
minimizerSurfaceArea = @(x) SurfaceArea(x(1), x(2), H);

% Initialize validSets array
validSets = [];

% Start timing
tic;

% Brute-force approach for obtaining valid sets
W_range = 12.0:0.001:96; % Adjust the range as needed
L_range = 12.0:0.001:96; % Adjust the range as needed

for W = W_range
    for L = L_range
        % Check constraints
        if W > 12 && W < 96 && L > 12 && L < 96
            % Check conditions using maximizer and minimizers
            if abs((maximizerBaseArea([W, L]) - minimizerVolume([W, L])) / minimizerVolume([W, L])) <= tolerance ...
                    && abs((maximizerBaseArea([W, L]) - minimizerSurfaceArea([W, L])) / minimizerSurfaceArea([W, L])) <= tolerance ...
                    && abs((minimizerVolume([W, L]) - minimizerSurfaceArea([W, L])) / minimizerSurfaceArea([W, L])) <= tolerance
                validSets = [validSets; W, L];
            end
        end
    end
end

% Display valid sets
disp('Valid sets of W and L:');
disp(validSets);

% Step 6: For loop
results = []; % Store results for CSV file

for i = 1:size(validSets, 1)
    W = validSets(i, 1);
    L = validSets(i, 2);

    % Calculate Maximum number of possible pipes that can be placed
    D = 1; % Adjust as needed
    maxPipes = (((W - 2*t) / D) - 1);

    % Check if maxPipes is an integer
    if ~isinteger(maxPipes)
        disp(['For W=', num2str(W), ', L=', num2str(L), ': Values not applicable']);
        continue;
    end

    % Check if maxPipes is odd or even
    if mod(maxPipes, 2) == 1
        % Calculate Maximum Number of Plants for odd
        maxPlants = ((L - 2*t) / (2 * D)) * Rounder((W - 2*t) / (2 * D));
    else
        % Calculate Maximum Number of Plants for even
        maxPlants = 0.5 * (((L - 2*t) / D) - 1) * ((W - 2*t) / D - 1);
    end

    % Print the result
    disp(['For W=', num2str(W), ', L=', num2str(L), ': Maximum Number of Plants = ', num2str(maxPlants)]);

    % Store results for CSV file
    results = [results; W, L, maxPlants];
end

% Stop timing
elapsedTime = toc;

% Display total execution time
disp(['Total Execution Time: ', num2str(elapsedTime), ' seconds']);

% Save results to CSV file
csvwrite('Optimal_Dimensions.csv', results);
disp('Results saved to Optimal_Dimensions.csv');