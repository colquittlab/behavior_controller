function trials = read_trials_from_file(fname)

fid = fopen(fname,'r');
count = 0;
file_line = fgets(fid);
while file_line > 0
    count = count + 1;
    [data, json] = parse_json(file_line);
    data = data{1};
    
    if isfield(data,'stimulus')
        trial.stimulus = data.stimulus;
    else
        trial.stimulus = '';
    end
    if isfield(data, 'start_time')
        trial.start_time = data.start_time;
    else
        trial.starttime = nan;
    end
    if isfield(data, 'stim_length')
        trial.stim_length = data.stim_length;
    else
        trial.stim_length = nan;
    end
    if isfield(data, 'stimset')
        trial.stimset = data.stimset;
    else
        trial.stimset = '';
    end
    if isfield(data, 'correct_answer')
        trial.correct_answer = data.correct_answer;
    else
        trial.correct_answer = '';
    end
    if isfield(data, 'stimset_idx')
        trial.stimset_idx = data.stimset_idx;
    else
        trial.stimset_idx = nan;
    end
    if isfield(data, 'result')
        trial.result = data.result;
        if strcmp(trial.result,'correct')
            trial.result_idx = 1;
        elseif strcmp(trial.result,'incorrect')
            trial.result_idx = 0;
        elseif strcmp(trial.result,'no_response')
            trial.result_idx = -1;
        end
    else
        trial.result = '';
        trial.result_idx = -2;
    end
    
    if isfield(data, 'response_time')
        trial.response_time = data.response_time;
    else
        trial.response_time = nan;
    end
    
    trials(count) = trial;
    
    file_line = fgets(fid);
end
fclose(fid);
end

