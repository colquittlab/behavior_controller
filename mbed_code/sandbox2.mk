
int wait_pi2 = 0
callback portin(2) up
	if wait_pi2 == 0 do
		wait_pi2 = 1
		sound('song1')
		do in 2000
			wait_pi2 = 0
		end
	end
end;
