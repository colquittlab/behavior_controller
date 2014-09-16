function data = read_config_file(fname)
if exist(fname)
    data = parse_file(fname,{'stimset_0','stimset_1','mode'});
end
end

%% subfunctions
function data=parse_file(filename,keywords)
% parse_file: parses a preferences file
% usage: file_struct=parse_file(filename,keywords)
%
% arguments (input)
% filename - character string containing the name of a
% preferences file. If this file is not on
% the path, then the name must also contain
% the full path to that file.
% keywords - cell array containing a list of legal
% keywords. keywords are not case sensitive,
% and only enough characters need be supplied
% make the choice of keyword un-ambiguous.


data = struct; 
% start by checking that the file exists at all
ex=exist(filename);
if ex~=2
  error(['File not found: ',filename])
end


% open file
fid=fopen(filename,'r');
% get one record at a time
flag=1;
while flag
    rec=fgetl(fid);
    if ~ischar(rec)
        % then it must have been and end-of-file(-1)
        flag=0;
    else
        if ~isempty(rec) % ignore empty lines
            if length(strfind(rec,'#'))>0
                idx = strfind(rec,'#');
                rec = rec(1:idx(1));
            end
            rec = strsplit(rec,'=');
            if length(rec)>=2
                key = strrep(rec{1},' ','');
                value = strrep(rec{2},' ','');
                data=setfield(data,key,value);
            end
                

        end
    end
end
% when all done, be nice and close the file
fclose(fid);
end
