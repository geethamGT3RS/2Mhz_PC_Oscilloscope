#echo this in red color "Open source software"
# echo 2 rows of - as border
echo "------------------------------------------------------------------------------"
echo -e "\e[31mOpen source software\e[0m"
echo "------------------------------------------------------------------------------"
echo "This is a script to run the oscilloscope"
echo "------------------------------------------------------------------------------"
echo -e "\e[31mDeveloped by: Geetham Talluri"
echo -e "Git Repository: https://github.com/geethamGT3RS/2Mhz_PC_Oscilloscope.git\e[0m"
echo "------------------------------------------------------------------------------"



gcc -o reciever reciever.c -lpwiringPi
taskset -c 0 ./reciever &
taskset -c 1 python3 server.py &