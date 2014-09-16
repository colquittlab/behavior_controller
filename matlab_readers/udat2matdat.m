function [mat_date, mat_dat_vec] = udat2matdat(unix_date)
unix_date = unix_date - 8*60*60; 
mat_date = (unix_date/86400)+datenum(1970,1,1);
if nargout > 1
    mat_dat_vec = datevec(mat_date);
end
end