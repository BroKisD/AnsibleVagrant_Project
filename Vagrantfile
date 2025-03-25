Vagrant.configure("2") do |config|
	config.vm.box = "ubuntu/focal64"

	config.vm.define "master" do |master|
		master.vm.hostname = "master"
		master.vm.network "private_network", ip: "192.168.56.10"
	end

	
	["slave1", "slave2"].each_with_index do |name, index|
		config.vm.define name do |slave|
			slave.vm.hostname = name
			slave.vm.network "private_network", ip: "192.168.56.#{11 + index}"
		end
	end
end

