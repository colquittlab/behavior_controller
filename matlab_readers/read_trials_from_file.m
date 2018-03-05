function trials = read_trials_from_file(fname,force_regenerate)
if nargin<2
force_regenerate = false; 
end
matfname = [fname '.mat'];

if (exist(matfname) && ~force_regenerate)
    filedata = dir(fname);
    data = load(matfname);
    if (~isfield(data, 'date_modified') || data.date_modified ~= filedata.datenum)
        trials = read_from_file(fname);
    else
        trials = data.trials;
    end
else
    trials = read_from_file(fname);
end
end

function trials = read_from_file(fname)
    file_data=dir(fname);
%     trials = struct
    date_modified = file_data.datenum;
    fid = fopen(fname,'r');
    count = 0;
    file_line = fgets(fid);
    while file_line > 0
        count = count + 1;
        try
            data = loadjson(file_line);
        catch
            data = loadjson(strrep(file_line,'null','[NaN, NaN]')); 
        end
%         data = data{1};
        
        if isfield(data,'stimulus')
            trial.stimulus = data.stimulus;
        else
            trial.stimulus = '';
        end
        if isfield(data, 'start_time')
            trial.start_time = data.start_time;
        else
            trial.start_time = nan;
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
            else
                trial.result_idx = -2;
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
        if isfield(data,'mode')
            trial.mode = data.mode;
        else
            trial.mode = '';
        end
        if isfield(data,'reward_p')
            if iscell(data.reward_p)
                trial.reward_p = cell2mat(data.reward_p);
            else
                trial.reward_p = data.reward_p;
            end
        else
            trial.reward_p = '';
        end
        if isfield(data,'track')
            trial.track.t = data.track(:,1);
            trial.track.t = trial.track.t;
            trial.track.uv = data.track(:,2:3); 
        else
            trial.track = '';
        end
        if isfield(data,'start_side')
             trial.start_side = data.start_side;
        else 
            trial.start_side = ''; 
        end
        if isfield(data,'playback_start_time')
            trial.playback_start_time = data.playback_start_time;
        else
            trial.playback_start_time = '';
        end
        if isfield(data, 'playbacks')
            trial.playbacks=data.playbacks;
        else
            trial.playbacks = '';
        end
        if isfield(data,'last_center_bin_entry_time')
            trial.last_center_bin_entry_time = data.last_center_bin_entry_time; 
        else
            trial.last_center_bin_entry_time = '';
        end
        if isfield(data, 'bin_entries')
            try
                trial.bin_entries = cell2mat(cellfun(@(x) [x{1} x{3}],data.bin_entries,'uniformoutput',false)');
            catch 
                bin_entries = {};
                bin_entries_string = data.bin_entries;  
                for k5=1:size(bin_entries_string,1)
                    bin_entries{end+1} = cellstr(bin_entries_string(k5,:));
       
                end
                
                trial.bin_entries = cell2mat(cellfun(@(x)([str2num(x{1}) str2num(x{3}) ]),bin_entries,'uniformoutput',false)');
            end
        else
            trial.bin_entries = '';
        end
        if isfield(data, 'stim_idxs')
            trial.stim_idxs = data.stim_idxs;
            
        else
            trial.stim_idxs = '';
        end
        
        try
            trials(count) = trial;
        catch
        end
        file_line = fgets(fid);
    end
    fclose(fid);
    if ~exist('trials')
        trials = [];
    end
    save([fname '.mat'],'trials','date_modified')
end
