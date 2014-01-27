int pi_wait_time = 200
int pi_song = 1
int pi_reward_a = 3
int pi_reward_b = 4

int feeder_port = 2
int feed_time = 2000
volume(255)


int box_state = 0
int random_pick = 0
int correct_ans = 0

callback portin(1) down
	portout(1) = 1
	sound(stop)
	sound(reset)
	portout(1) = 0
	box_state = 0
end;

int wait_pi2 = 0
callback portin(2) up
	if wait_pi2 == 0 do
		wait_pi2  = 1
		do in 200
			wait_pi2 = 0
		end
		if box_state == 0 do
			box_state = 1

			random_pick = random(1)

			if random_pick == 0 do
				sound('song1')
				correct_ans = 0
			else if random_pick == 1 do
				sound('song2')
				correct_ans = 1
			end
			disp('playing song!')
			do in 1000
				box_state = 2
			end
		end
	end
end;


int wait_pi3 = 0
callback portin(3) up
	if wait_pi3 == 0 do
		wait_pi3 = 1
		do in 200
			wait_pi3 = 0
		end
		disp('reward-A depressed')
		if box_state == 2 do
			disp('-Evaluating Response')
			if correct_ans == 0 do
				disp('-correct anwser, rewarding')
				box_state = 3
				portout(2) = 1 
				do in 2000
					portout(2) = 0
				end
			else do 
				disp('Incorrect anwser, entering timeout')
			end
		else do
			disp('-Ignored, wrong box_state')
		end 
	end
end;



